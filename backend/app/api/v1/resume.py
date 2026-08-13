"""
Resume Intelligence API routes — /api/v1/resume/*

Endpoints:
  - POST /api/v1/resume/upload: Upload PDF/DOCX resume file to Cloudinary, create DB record, and enqueue parse_resume job.
  - GET /api/v1/resume: List all resumes owned by current authenticated user.
  - POST /api/v1/resume/{resume_id}/score: Queue resume ATS scoring & grammar audit job.
  - POST /api/v1/resume/{resume_id}/job-description: Submit target job description text & queue keyword gap analysis.
  - GET /api/v1/resume/{resume_id}/report: Fetch latest resume evaluation report.
  - GET /api/v1/resume/jobs/{job_id}: Poll job processing status.
  - GET /api/v1/resume/{resume_id}: Fetch resume record by ID for the authenticated user.
"""

import logging
from uuid import UUID

from arq.jobs import Job, JobStatus
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.core.limiter import limiter
from app.core.redis_pool import get_redis_pool
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
    """Enqueue parse_resume via the shared Arq pool. Raises HTTPException(503)
    if the queue is unavailable — never fabricates a job_id, since a fake ID
    can never be enqueued and will silently never run."""
    try:
        redis = get_redis_pool()
        job = await redis.enqueue_job("parse_resume", str(resume_id))
    except Exception as exc:
        logger.error(f"Failed to enqueue parse_resume for resume_id={resume_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Background processing is temporarily unavailable. Try again in a moment.",
        )
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not enqueue resume parsing job.",
        )
    return job.job_id


async def _enqueue_score_job(resume_id: UUID) -> str:
    """Enqueue score_resume via the shared Arq pool. See _enqueue_parse_job
    for the no-fake-id, no-silent-fallback rule."""
    try:
        redis = get_redis_pool()
        job = await redis.enqueue_job("score_resume", str(resume_id))
    except Exception as exc:
        logger.error(f"Failed to enqueue score_resume for resume_id={resume_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Background processing is temporarily unavailable. Try again in a moment.",
        )
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not enqueue resume scoring job.",
        )
    return job.job_id


async def _enqueue_analyze_keywords_job(job_description_id: UUID, resume_id: UUID) -> str:
    """Enqueue analyze_keywords via the shared Arq pool. See _enqueue_parse_job
    for the no-fake-id, no-silent-fallback rule."""
    try:
        redis = get_redis_pool()
        job = await redis.enqueue_job("analyze_keywords", str(job_description_id), str(resume_id))
    except Exception as exc:
        logger.error(f"Failed to enqueue analyze_keywords for jd_id={job_description_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Background processing is temporarily unavailable. Try again in a moment.",
        )
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not enqueue keyword analysis job.",
        )
    return job.job_id


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume file",
    description="Uploads a PDF or DOCX resume file to Cloudinary storage, creates a database record, and enqueues background parsing.",
)
@limiter.limit("10/hour")
async def upload_resume(
    request: Request,
    file: UploadFile = File(..., description="Resume file (PDF or DOCX format)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeUploadResponse:
    """
    Accepts an uploaded resume file (PDF or DOCX), uploads it to Cloudinary,
    inserts a record in the database, and enqueues the `parse_resume` background job.
    Rate limited to 10 uploads per hour per user.
    """
    resume = await resume_service.upload_resume_file(
        file=file,
        user_id=current_user.id,
        db=db,
    )

    job_id = await _enqueue_parse_job(resume.id)

    return ResumeUploadResponse(
        resume_id=resume.id,
        file_url=resume_service.get_effective_resume_file_url(resume),
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
    response_list = []
    for r in resumes:
        resp = ResumeResponse.model_validate(r)
        resp.file_url = resume_service.get_effective_resume_file_url(r)
        response_list.append(resp)
    return response_list


@router.post(
    "/{resume_id}/score",
    response_model=ScoreResumeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue resume ATS scoring & grammar audit",
    description="Enqueues the score_resume background job for a parsed resume.",
)
@limiter.limit("20/hour")
async def score_resume_endpoint(
    request: Request,
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScoreResumeResponse:
    """
    Verifies resume ownership and enqueues the `score_resume` background job.
    Rate limited to 20 per hour per user.
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
@limiter.limit("20/hour")
async def submit_job_description(
    request: Request,
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
    Never reports a status other than what Arq actually says. A job that
    doesn't exist (not_found) or a Redis outage are both surfaced as
    status='failed' with a clear message — they are NOT reported as
    'complete', since that previously caused the frontend to display stale
    or missing data as if processing had genuinely finished.
    """
    try:
        redis = get_redis_pool()
    except RuntimeError as exc:
        logger.error(f"Redis pool unavailable while checking job_id={job_id}: {exc}")
        return JobStatusResponse(
            job_id=job_id,
            status="failed",
            result={"error": "Background job queue is unreachable. Check server logs and Redis connectivity."},
        )

    try:
        job = Job(job_id, redis)
        arq_status = await job.status()
        result = None

        if arq_status == JobStatus.complete:
            try:
                res = await job.result()
                result = res if isinstance(res, dict) else {"output": str(res)}
            except Exception as exc:
                logger.error(f"Job {job_id} reported complete but result() raised: {exc}")
                return JobStatusResponse(
                    job_id=job_id,
                    status="failed",
                    result={"error": "Job finished but its result could not be read. Check server logs."},
                )
            status_str = "complete"
        elif arq_status in (JobStatus.queued, JobStatus.deferred):
            status_str = "queued"
        elif arq_status == JobStatus.in_progress:
            status_str = "in_progress"
        elif arq_status == JobStatus.not_found:
            status_str = "failed"
            result = {"error": "Job not found. It may have expired, or was never successfully enqueued."}
        else:
            status_str = "failed"

        return JobStatusResponse(job_id=job_id, status=status_str, result=result)
    except Exception as exc:
        logger.error(f"Error checking job status for job_id={job_id}: {exc}")
        return JobStatusResponse(
            job_id=job_id,
            status="failed",
            result={"error": "Could not check job status. Check server logs and Redis connectivity."},
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

    resp = ResumeResponse.model_validate(resume)
    resp.file_url = resume_service.get_effective_resume_file_url(resume)
    return resp
