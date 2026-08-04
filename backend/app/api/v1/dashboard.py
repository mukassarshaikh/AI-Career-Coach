"""
Dashboard API routes — /api/v1/dashboard/*

Endpoints:
  - GET /api/v1/dashboard/summary: Consolidated overview of resume score, skill gaps, roadmap progress.
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services import dashboard_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard summary",
    description="Returns consolidated overview metrics including ATS resume score, missing skill count, and active roadmap completion progress.",
)
async def get_dashboard_summary_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummaryResponse:
    """
    Returns dashboard summary data for the authenticated user.
    """
    return await dashboard_service.get_user_dashboard_summary(
        db=db,
        user_id=current_user.id,
    )
