"""
dashboard_service.py — Business logic for platform consolidated dashboard metrics.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career import ChatSession
from app.models.resume import Resume
from app.models.skill import SkillGapReport
from app.schemas.dashboard import DashboardSummaryResponse
from app.services import learning_service

logger = logging.getLogger(__name__)


async def get_user_dashboard_summary(
    db: AsyncSession,
    user_id: UUID,
) -> DashboardSummaryResponse:
    """
    Consolidates candidate status across Resume, Skill, Learning, and Career Intelligence engines.
    """
    # 1. Fetch latest resume ATS score
    resume_stmt = (
        select(Resume.ats_score)
        .where(Resume.user_id == user_id, Resume.ats_score.isnot(None))
        .order_by(Resume.created_at.desc())
        .limit(1)
    )
    resume_res = await db.execute(resume_stmt)
    latest_ats_score = resume_res.scalar_one_or_none()

    # 2. Fetch latest skill gap report
    gap_stmt = (
        select(SkillGapReport)
        .where(SkillGapReport.user_id == user_id)
        .order_by(SkillGapReport.created_at.desc())
        .limit(1)
    )
    gap_res = await db.execute(gap_stmt)
    latest_gap_report = gap_res.scalar_one_or_none()

    missing_count = 0
    target_role = None
    if latest_gap_report:
        target_role = latest_gap_report.target_role
        if isinstance(latest_gap_report.missing_skills, list):
            missing_count = len(latest_gap_report.missing_skills)

    # 3. Fetch active roadmap
    active_roadmap = await learning_service.get_active_roadmap_by_user_id(db=db, user_id=user_id)

    total_items = 0
    completed_items = 0
    percentage = 0.0
    active_roadmap_id = None

    if active_roadmap:
        active_roadmap_id = active_roadmap.id
        items = active_roadmap.items or []
        total_items = len(items)
        completed_items = sum(1 for item in items if item.status == "completed")
        if total_items > 0:
            percentage = round((completed_items / total_items) * 100, 1)

    # 4. Fetch Career Chat Sessions
    chat_stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
    )
    chat_res = await db.execute(chat_stmt)
    chat_sessions = list(chat_res.scalars().all())
    chat_sessions_count = len(chat_sessions)
    latest_chat_session_id = chat_sessions[0].id if chat_sessions else None

    return DashboardSummaryResponse(
        resume_score=latest_ats_score,
        missing_skills_count=missing_count,
        target_role=target_role,
        roadmap_total_items=total_items,
        roadmap_completed_items=completed_items,
        roadmap_completion_percentage=percentage,
        active_roadmap_id=active_roadmap_id,
        chat_sessions_count=chat_sessions_count,
        latest_chat_session_id=latest_chat_session_id,
    )

