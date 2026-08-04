"""
recalculate_skill_vector.py — Arq worker job definition (Phase 2 Story 2).

Consumes queued skill vector recalculation jobs from Redis when a user completes a roadmap item:
  1. Loads the user's most recent parsed resume.
  2. Calls skill_service.upsert_user_skill_vector() to update the 384-dim skill vector embedding.
  3. Calls skill_service.compute_user_skill_gap() for target_role to produce an updated SkillGapReport.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from app.models.resume import Resume
from app.services import skill_service

logger = logging.getLogger(__name__)


async def recalculate_skill_vector(ctx: dict, user_id: str, target_role: str) -> dict:
    """
    Arq worker job that recalculates a user's skill vector and updates their skill gap report
    after a roadmap item is completed.

    Args:
        ctx: Arq context dictionary containing 'db_factory'.
        user_id: String UUID of the user.
        target_role: Target job title / role string.

    Returns:
        Summary dict containing status, user_id, target_role, and new_skill_gap_report_id.
    """
    logger.info(f"Starting recalculate_skill_vector job for user_id={user_id}, target_role='{target_role}'")

    db_factory = ctx.get("db_factory")
    if not db_factory:
        raise RuntimeError("Arq context missing 'db_factory'")

    async with db_factory() as db:
        user_uuid = UUID(user_id)

        # 1. Fetch user's latest parsed resume
        stmt = (
            select(Resume)
            .where(Resume.user_id == user_uuid, Resume.parsed_json.isnot(None))
            .order_by(Resume.created_at.desc())
            .limit(1)
        )
        res = await db.execute(stmt)
        resume = res.scalar_one_or_none()

        if not resume:
            logger.error(f"Cannot recalculate skill vector for user {user_id}: no parsed resume found.")
            return {
                "status": "failed",
                "error": f"No parsed resume found for user {user_id}.",
                "user_id": user_id,
            }

        try:
            # 2. Re-embed user's skills using latest resume data
            updated_vector = await skill_service.upsert_user_skill_vector(db=db, resume=resume)

            # 3. Re-run compute_user_skill_gap for target_role
            gap_report = await skill_service.compute_user_skill_gap(
                db=db,
                user_id=user_uuid,
                target_role=target_role,
            )

            logger.info(
                f"Completed recalculate_skill_vector job for user_id={user_id}: new_skill_gap_report_id={gap_report.id}"
            )
            return {
                "status": "complete",
                "user_id": user_id,
                "target_role": target_role,
                "new_skill_gap_report_id": str(gap_report.id),
            }
        except Exception as exc:
            logger.error(f"Failed recalculate_skill_vector job for user {user_id}: {exc}")
            return {
                "status": "failed",
                "error": f"Recalculation failed: {exc}",
                "user_id": user_id,
            }
