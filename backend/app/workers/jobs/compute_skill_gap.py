"""
compute_skill_gap.py — Arq worker job definition (Phase 1).

Consumes queued skill gap computation jobs from Redis:
  1. Loads user's SkillVector record from Postgres (fails cleanly if none exists).
  2. Queries MarketSkillReference table for target_role.
  3. Identifies missing competencies and ranks them by market demand_weight.
  4. Inserts a new `skill_gap_reports` record.
"""

import logging
from uuid import UUID

from app.services import skill_service

logger = logging.getLogger(__name__)


async def compute_skill_gap(ctx: dict, user_id: str, target_role: str) -> dict:
    """
    Arq worker job that computes a skill gap report for a candidate against a target role.

    Args:
        ctx: Arq context dictionary containing 'db_factory'.
        user_id: String UUID of the user.
        target_role: Target job title / role string.

    Returns:
        Summary dict containing status, user_id, target_role, report_id, and missing_count.
    """
    logger.info(f"Starting compute_skill_gap job for user_id={user_id}, target_role='{target_role}'")

    db_factory = ctx.get("db_factory")
    if not db_factory:
        raise RuntimeError("Arq context missing 'db_factory'")

    async with db_factory() as db:
        try:
            report = await skill_service.compute_user_skill_gap(
                db=db,
                user_id=UUID(user_id),
                target_role=target_role,
            )
        except Exception as exc:
            logger.error(f"Failed to compute skill gap for user {user_id} and role '{target_role}': {exc}")
            return {"status": "failed", "error": f"Skill gap computation failed: {exc}"}

        missing_count = len(report.missing_skills) if isinstance(report.missing_skills, list) else 0
        logger.info(
            f"Completed compute_skill_gap job for user_id={user_id}, report_id={report.id}, missing_count={missing_count}"
        )
        return {
            "status": "complete",
            "user_id": user_id,
            "target_role": target_role,
            "report_id": str(report.id),
            "missing_count": missing_count,
        }
