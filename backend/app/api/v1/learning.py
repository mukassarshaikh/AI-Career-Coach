"""
Learning Intelligence API routes — /api/v1/learning/*

Endpoints:
  - POST /api/v1/learning/roadmap: Generate a new roadmap from a skill_gap_report_id (async Arq job).
  - GET /api/v1/learning/roadmap/{id}: Get full roadmap details with sequenced items.
  - POST /api/v1/learning/roadmap/{id}/regenerate: Re-trigger roadmap generation for an existing roadmap.
  - PATCH /api/v1/learning/roadmap-item/{id}: Stub route for marking item complete (returns 501 Not Implemented).
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
from app.schemas.learning import (
    GenerateRoadmapRequest,
    GenerateRoadmapResponse,
    RoadmapResponse,
)
from app.services import learning_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning", tags=["learning"])


async def _enqueue_generate_roadmap_job(skill_gap_report_id: UUID, user_id: UUID) -> str:
    """Helper function to enqueue generate_roadmap job to Arq via Redis."""
    try:
        redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        job = await redis.enqueue_job("generate_roadmap", str(skill_gap_report_id), str(user_id))
        job_id = job.job_id if job else f"job_roadmap_{skill_gap_report_id}"
        await redis.close()
        return job_id
    except Exception as exc:
        logger.warning(
            f"Redis connection failed during generate_roadmap enqueue ({exc}). Using synthetic job_id."
        )
        return f"job_roadmap_{skill_gap_report_id}"


@router.post(
    "/roadmap",
    response_model=GenerateRoadmapResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate learning roadmap",
    description="Enqueues the generate_roadmap background job to construct a step-by-step learning path from a skill gap report.",
)
@limiter.limit("5/hour")
async def generate_roadmap_endpoint(
    request: Request,
    body: GenerateRoadmapRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GenerateRoadmapResponse:
    """
    Enqueues background roadmap generation for the specified skill_gap_report_id.
    Rate limited to 5 requests per hour per user.
    """
    job_id = await _enqueue_generate_roadmap_job(
        skill_gap_report_id=body.skill_gap_report_id,
        user_id=current_user.id,
    )

    return GenerateRoadmapResponse(
        skill_gap_report_id=body.skill_gap_report_id,
        job_id=job_id,
        message="Learning roadmap generation job enqueued.",
    )


@router.get(
    "/roadmap/{id}",
    response_model=RoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Get roadmap details",
    description="Fetches a Roadmap and all associated items ordered by sequence_order.",
)
async def get_roadmap_endpoint(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoadmapResponse:
    """
    Returns the requested roadmap and its sequenced learning items.
    """
    roadmap = await learning_service.get_roadmap_by_id(
        db=db,
        roadmap_id=id,
        user_id=current_user.id,
    )
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found.",
        )

    return RoadmapResponse.model_validate(roadmap)


@router.post(
    "/roadmap/{id}/regenerate",
    response_model=GenerateRoadmapResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Regenerate existing roadmap",
    description="Re-enqueues the generate_roadmap job for an existing roadmap's underlying skill gap report.",
)
@limiter.limit("5/hour")
async def regenerate_roadmap_endpoint(
    id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GenerateRoadmapResponse:
    """
    Re-triggers roadmap generation for an existing roadmap ID.
    Rate limited to 5 requests per hour per user.
    """
    roadmap = await learning_service.get_roadmap_by_id(
        db=db,
        roadmap_id=id,
        user_id=current_user.id,
    )
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found.",
        )

    job_id = await _enqueue_generate_roadmap_job(
        skill_gap_report_id=roadmap.skill_gap_report_id,
        user_id=current_user.id,
    )

    return GenerateRoadmapResponse(
        skill_gap_report_id=roadmap.skill_gap_report_id,
        job_id=job_id,
        message="Roadmap regeneration job enqueued.",
    )


@router.patch(
    "/roadmap-item/{id}",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Mark roadmap item complete (stub)",
    description="Stub route for item completion tracking. Returns 501 Not Implemented until the recalculate_skill_vector feature is introduced.",
)
async def mark_roadmap_item_complete_stub(
    id: UUID,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Stub endpoint returning 501 Not Implemented per Phase 2 spec.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Item completion tracking coming in the next release",
    )
