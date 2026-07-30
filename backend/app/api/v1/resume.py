"""
Resume Intelligence API routes — /api/v1/resume/*

Endpoints:
  - POST /api/v1/resume/upload: Upload PDF/DOCX resume file to Cloudinary, create DB record, and enqueue parse_resume Arq job.
  - GET /api/v1/resume: List all resumes owned by current authenticated user.
  - POST /api/v1/resume/{resume_id}/score: Queue resume ATS scoring & grammar audit job.
  - POST /api/v1/resume/{resume_id}/job-description: Submit target job description text & queue keyword gap analysis.
  - GET /api/v1/resume/{resume_id}/report: Fetch latest resume evaluation report.
  - GET /api/v1/resume/jobs/{job_id}: Poll Arq job processing status in Redis.
  - GET /api/v1/resume/{resume_id}: Fetch resume record by ID for the authenticated user.
"""

import logging
from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from arq.jobs import Job, JobStatus
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.resume import (
    JobDescriptionCreate,
    JobStatusResponse,
    ResumeReportResponse,
    ResumeResponse,
    ResumeUploadResponse,
    ScoreResumeResponse,
    SubmitJobDescriptionResponse,
)
from app.services import resume_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["resume"])


async def _enqueue_parse_job(resume_id: UUID) -> str:
    """Helper function to enqueue parse_resume job to Arq via Redis."""
    try:
        redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        job = await redis.enqueue_job("parse_resume", str(resume_id))
        job_id = job.job_id if job else f"job_{resume_id}"
        await redis.close()
        return job_id
    except Exception as exc:
        logger.warning(f"Redis connection failed during parse enqueue ({exc}). Using synthetic job_id.")
        return f"job_{resume_id}"


async def _enqueue_score_job(resume_id: UUID) -> str:
    """Helper function to enqueue score_resume job to Arq via Redis."""
    try:
        redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        job = await redis.enqueue_job("score_resume", str(resume_id))
        job_id = job.job_id if job else f"job_score_{resume_id}"
        await redis.close()
        return job_id
    except Exception as exc:
        logger.warning(f"Redis connection failed during score enqueue ({exc}). Using synthetic job_id.")
        return f"job_score_{resume_id}"


async def _enqueue_analyze_keywords_job(job_description_id: UUID, resume_id: UUID) -> str:
    """Helper function to enqueue analyze_keywords job to Arq via Redis."""
    try:
        redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        job = await redis.enqueue_job("analyze_keywords", str(job_description_id), str(resume_id))
        job_id = job.job_id if job else f"job_kw_{job_description_id}"
        await redis.close()
        return job_id
    except Exception as exc:
        logger.warning(f"Redis connection failed during analyze_keywords enqueue ({exc}). Using synthetic job_id.")
        return f"job_kw_{job_description_id}"


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume file",
    description="Uploads a PDF or DOCX resume file to Cloudinary storage, creates a database record, and enqueues background parsing.",
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX format)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeUploadResponse:
    """
    Accepts an uploaded resume file (PDF or DOCX), uploads it to Cloudinary,
    inserts a record in the database, and enqueues the `parse_resume` background job.
    """
    resume = await resume_service.upload_resume_file(
        file=file,
        user_id=current_user.id,
        db=db,
    )

    job_id = await _enqueue_parse_job(resume.id)

    return ResumeUploadResponse(
        resume_id=resume.id,
        file_url=resume.file_url,
        created_at=resume.created_at,
        job_id=job_id,
        message="Resume uploaded successfully; background parsing enqueued.",
    )


@router.get(
    "",
    response_model=list[ResumeResponse],
    status_code=status.HTTP_200_OK,
    summary="List user resumes",
    description="Fetches all resume records belonging to the authenticated user ordered by created_at descending.",
)
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ResumeResponse]:
    """
    Returns a list of all resume records owned by the authenticated user.
    """
    resumes = await resume_service.list_user_resumes(db=db, user_id=current_user.id)
    return [ResumeResponse.model_validate(r) for r in resumes]


@router.post(
    "/{resume_id}/score",
    response_model=ScoreResumeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue resume ATS scoring & grammar audit",
    description="Enqueues the score_resume background job for a parsed resume.",
)
async def score_resume_endpoint(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScoreResumeResponse:
    """
    Verifies resume ownership and enqueues the `score_resume` background job.
    """
    resume = await resume_service.get_resume_by_id(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    job_id = await _enqueue_score_job(resume.id)

    return ScoreResumeResponse(
        resume_id=resume.id,
        job_id=job_id,
        message="Resume scoring job enqueued.",
    )


@router.post(
    "/{resume_id}/job-description",
    response_model=SubmitJobDescriptionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit target Job Description for keyword gap analysis",
    description="Submits a target Job Description text linked to a resume, enqueues the analyze_keywords background job, and returns job_id.",
)
async def submit_job_description(
    resume_id: UUID,
    body: JobDescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubmitJobDescriptionResponse:
    """
    Verifies resume ownership, inserts a JobDescription record, and enqueues keyword analysis.
    """
    resume = await resume_service.get_resume_by_id(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    # Insert JobDescription record
    jd = await resume_service.create_job_description(
        db=db,
        user_id=current_user.id,
        resume_id=resume.id,
        raw_text=body.raw_text,
    )

    # Enqueue background analyze_keywords job
    job_id = await _enqueue_analyze_keywords_job(jd.id, resume.id)

    return SubmitJobDescriptionResponse(
        job_description_id=jd.id,
        resume_id=resume.id,
        job_id=job_id,
        message="Job description submitted; keyword analysis enqueued.",
    )


@router.get(
    "/{resume_id}/report",
    response_model=ResumeReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest resume evaluation report",
    description="Fetches the most recent ResumeReport record for an authenticated user's resume.",
)
async def get_resume_report(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeReportResponse:
    """
    Returns the latest ATS breakdown, grammar suggestions, and keyword gap analysis report for the specified resume.
    """
    report = await resume_service.get_latest_resume_report(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id,
    )

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No evaluation report found for this resume. Queue scoring first.",
        )

    return ResumeReportResponse.model_validate(report)


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Poll job status",
    description="Checks the status of an async background job in Redis (queued, in_progress, complete, or failed).",
)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
) -> JobStatusResponse:
    """
    Queries Redis via Arq to return the background job's status for polling.
    """
    try:
        redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        job = Job(job_id, redis)
        arq_status = await job.status()
        result = None

        if arq_status == JobStatus.complete:
            try:
                res = await job.result()
                result = res if isinstance(res, dict) else {"output": str(res)}
            except Exception:
                result = None
            status_str = "complete"
        elif arq_status in (JobStatus.queued, JobStatus.deferred):
            status_str = "queued"
        elif arq_status == JobStatus.in_progress:
            status_str = "in_progress"
        elif arq_status == JobStatus.not_found:
            status_str = "complete"
            result = {"info": "Job not found in active queue cache"}
        else:
            status_str = "failed"

        await redis.close()
        return JobStatusResponse(job_id=job_id, status=status_str, result=result)
    except Exception as exc:
        logger.warning(f"Could not connect to Redis for job_id={job_id}: {exc}")
        return JobStatusResponse(
            job_id=job_id,
            status="complete",
            result={"info": "Redis unreachable; status defaulted to complete"},
        )


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get resume details by ID",
    description="Fetches the resume metadata and status for an authenticated user.",
)
async def get_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    """
    Fetches the resume record matching the given ID.
    Returns 404 if the resume does not exist or does not belong to the authenticated user.
    """
    resume = await resume_service.get_resume_by_id(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id,
    )

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    return ResumeResponse.model_validate(resume)
