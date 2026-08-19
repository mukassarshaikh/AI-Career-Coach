"""
user_service.py — User management & GDPR compliance services (Phase 4 Story 4.3).

Handles:
  - GDPR Right to Erasure: transactional deletion of user account and all associated
    owned data across all database tables (resumes, job_descriptions, resume_reports,
    skill_vectors, skill_gap_reports, roadmaps, roadmap_items, chat_sessions,
    chat_messages, ai_generation_logs, users).
  - Cloudinary asset destruction for all raw resume files owned by the user.
"""

import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career import ChatMessage, ChatSession
from app.models.learning import Roadmap, RoadmapItem
from app.models.logs import AiGenerationLog
from app.models.resume import JobDescription, Resume, ResumeReport
from app.models.skill import SkillGapReport, SkillVector
from app.models.user import User
from app.services import resume_service

logger = logging.getLogger(__name__)


async def delete_user_account(db: AsyncSession, user_id: UUID) -> dict:
    """
    Executes a complete, transactional GDPR Article 17 Right to Erasure operation
    for the authenticated candidate user.

    Steps:
      1. Identifies and destroys all Cloudinary resume assets owned by the user.
      2. Deletes all user-owned data across all tables in strict dependency-safe order.
      3. Deletes the core `users` record.
      4. Atomically commits the transaction or rolls back on any error.

    Returns:
      {"deleted": True}
    """
    logger.info(f"Initiating GDPR account deletion for user_id={user_id}")

    try:
        # 1. Fetch user's resumes to collect Cloudinary asset info for asset purging
        stmt_resumes = select(Resume).where(Resume.user_id == user_id)
        res_resumes = await db.execute(stmt_resumes)
        user_resumes = list(res_resumes.scalars().all())

        # 2. Attempt Cloudinary asset destruction for all user resumes BEFORE database erasure
        failed_assets = []
        for r in user_resumes:
            pub_id, delivery_type = resume_service.extract_cloudinary_info_from_resume(r)
            if pub_id:
                del_result = resume_service.delete_cloudinary_asset(
                    public_id=pub_id,
                    resource_type="raw",
                    delivery_type=delivery_type,
                )
                if del_result.get("status") == "failed":
                    failed_assets.append((pub_id, del_result.get("error")))

        if failed_assets:
            error_details = ", ".join([f"'{pub_id}' ({err})" for pub_id, err in failed_assets])
            logger.error(
                f"Aborting GDPR erasure for user_id={user_id}: Cloudinary asset deletion failed for: {error_details}"
            )
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to delete remote resume asset from Cloudinary: {error_details}. User data deletion aborted to preserve data integrity.",
            )

        # 3. Dependency-safe table deletion inside single atomic transaction
        # Delete user's AI generation logs
        await db.execute(
            delete(AiGenerationLog).where(AiGenerationLog.user_id == user_id)
        )

        # Delete chat messages belonging to user's chat sessions
        await db.execute(
            delete(ChatMessage).where(
                ChatMessage.session_id.in_(
                    select(ChatSession.id).where(ChatSession.user_id == user_id)
                )
            )
        )

        # Delete chat sessions
        await db.execute(delete(ChatSession).where(ChatSession.user_id == user_id))

        # Delete roadmap items belonging to user's roadmaps
        await db.execute(
            delete(RoadmapItem).where(
                RoadmapItem.roadmap_id.in_(
                    select(Roadmap.id).where(Roadmap.user_id == user_id)
                )
            )
        )

        # Delete roadmaps
        await db.execute(delete(Roadmap).where(Roadmap.user_id == user_id))

        # Delete skill gap reports
        await db.execute(
            delete(SkillGapReport).where(SkillGapReport.user_id == user_id)
        )

        # Delete skill vectors
        await db.execute(delete(SkillVector).where(SkillVector.user_id == user_id))

        # Delete resume reports belonging to user's resumes
        await db.execute(
            delete(ResumeReport).where(
                ResumeReport.resume_id.in_(
                    select(Resume.id).where(Resume.user_id == user_id)
                )
            )
        )

        # Delete target job descriptions
        await db.execute(
            delete(JobDescription).where(JobDescription.user_id == user_id)
        )

        # Delete resumes
        await db.execute(delete(Resume).where(Resume.user_id == user_id))

        # Delete the core user record
        await db.execute(delete(User).where(User.id == user_id))

        # Commit transaction
        await db.commit()
        logger.info(f"Successfully erased all data for user_id={user_id}")
        return {"deleted": True}

    except Exception as exc:
        await db.rollback()
        logger.error(f"Account erasure transaction failed for user_id={user_id}: {exc}")
        raise exc
