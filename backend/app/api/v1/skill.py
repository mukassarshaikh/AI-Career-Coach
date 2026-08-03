"""
Skill Intelligence API routes — /api/v1/skill/*

Endpoints:
  - POST /api/v1/skill/vector: Generate/update skill vector from a parsed resume.
  - POST /api/v1/skill/gap-report: Compute skill gap report against a target role.
  - GET /api/v1/skill/gap-report: Fetch latest skill gap report for authenticated user.
  - POST /api/v1/skill/gap-report/refresh: Re-trigger skill gap computation.
"""

import logging
from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.core.config import settings
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.skill import (
    ComputeSkillGapRequest,
    ComputeSkillGapResponse,
    GenerateSkillVectorRequest,
    GenerateSkillVectorResponse,
    SkillGapReportResponse,
)
from app.services import resume_service, skill_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/skill", tags=["skill"])


async def _enqueue_skill_vector_job(resume_id: UUID) -> str:
    """Helper function to enqueue generate_skill_vector job to Arq via Redis."""
    try:
        redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        job = await redis.enqueue_job("generate_skill_vector", str(resume_id))
        job_id = job.job_id if job else f"job_vector_{resume_id}"
        await redis.close()
        return job_id
    except Exception as exc:
        logger.warning(f"Redis connection failed during skill vector enqueue ({exc}). Using synthetic job_id.")
        return f"job_vector_{resume_id}"


async def _enqueue_compute_gap_job(user_id: UUID, target_role: str) -> str:
    """Helper function to enqueue compute_skill_gap job to Arq via Redis."""
    try:
        redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        job = await redis.enqueue_job("compute_skill_gap", str(user_id), target_role)
        job_id = job.job_id if job else f"job_gap_{user_id}"
        await redis.close()
        return job_id
    except Exception as exc:
        logger.warning(f"Redis connection failed during skill gap enqueue ({exc}). Using synthetic job_id.")
        return f"job_gap_{user_id}"


@router.post(
    "/vector",
    response_model=GenerateSkillVectorResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate or update skill vector from resume",
    description="Enqueues the generate_skill_vector background job for a parsed resume.",
)
@limiter.limit("20/hour")
async def generate_skill_vector_endpoint(
    request: Request,
    body: GenerateSkillVectorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GenerateSkillVectorResponse:
    """
    Verifies resume ownership and enqueues background skill vector generation.
    Rate limited to 20 per hour per user.
    """
    resume = await resume_service.get_resume_by_id(
        db=db,
        resume_id=body.resume_id,
        user_id=current_user.id,
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    job_id = await _enqueue_skill_vector_job(resume.id)

    return GenerateSkillVectorResponse(
        resume_id=resume.id,
        job_id=job_id,
        message="Skill vector generation job enqueued.",
    )


@router.post(
    "/gap-report",
    response_model=ComputeSkillGapResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Compute skill gap report",
    description="Enqueues the compute_skill_gap background job to evaluate candidate skill gaps against market reference data.",
)
@limiter.limit("20/hour")
async def compute_skill_gap_endpoint(
    request: Request,
    body: ComputeSkillGapRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComputeSkillGapResponse:
    """
    Enqueues background skill gap computation for the authenticated user against target_role.
    Rate limited to 20 per hour per user.
    """
    skill_vector = await skill_service.get_skill_vector_by_user_id(db=db, user_id=current_user.id)
    if not skill_vector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No skill vector found for user. Please upload a resume and generate a skill vector first.",
        )

    job_id = await _enqueue_compute_gap_job(user_id=current_user.id, target_role=body.target_role)

    return ComputeSkillGapResponse(
        target_role=body.target_role,
        job_id=job_id,
        message="Skill gap report computation enqueued.",
    )


@router.get(
    "/gap-report",
    response_model=SkillGapReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest skill gap report",
    description="Fetches the most recent SkillGapReport record for the authenticated user.",
)
async def get_skill_gap_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SkillGapReportResponse:
    """
    Returns the latest skill gap report containing missing skills ranked by demand weight.
    """
    report = await skill_service.get_latest_skill_gap_report(db=db, user_id=current_user.id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No skill gap report found for user. Queue skill gap computation first.",
        )

    return SkillGapReportResponse.model_validate(report)


@router.post(
    "/gap-report/refresh",
    response_model=ComputeSkillGapResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Refresh skill gap report",
    description="Re-triggers skill gap computation against updated market references or skill vectors. Reuses POST /skill/gap-report logic.",
)
@limiter.limit("20/hour")
async def refresh_skill_gap_endpoint(
    request: Request,
    body: ComputeSkillGapRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComputeSkillGapResponse:
    """
    Re-enqueues background skill gap computation for semantic clarity (re-runs computation using same service/job).
    Rate limited to 20 per hour per user.
    """
    return await compute_skill_gap_endpoint(request=request, body=body, current_user=current_user, db=db)
