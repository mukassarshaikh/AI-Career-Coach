"""
generate_roadmap.py — Arq worker job definition (Phase 2).

Consumes queued learning roadmap generation jobs from Redis:
  1. Loads SkillGapReport by skill_gap_report_id.
  2. Confirms missing_skills is non-empty (fails cleanly if empty/null or not found).
  3. Archives any existing 'active' roadmap for the user.
  4. Generates sequenced roadmap items via Groq LLM.
  5. Inserts new `roadmaps` and `roadmap_items` records in Postgres.
"""

import logging
from uuid import UUID

from app.services import learning_service

logger = logging.getLogger(__name__)


async def generate_roadmap(ctx: dict, skill_gap_report_id: str, user_id: str) -> dict:
    """
    Arq worker job that generates a step-by-step learning roadmap for a skill gap report.

    Args:
        ctx: Arq context dictionary containing 'db_factory'.
        skill_gap_report_id: String UUID of the SkillGapReport.
        user_id: String UUID of the user.

    Returns:
        Summary dict containing status, user_id, skill_gap_report_id, roadmap_id, and items_count.
    """
    logger.info(
        f"Starting generate_roadmap job for skill_gap_report_id={skill_gap_report_id}, user_id={user_id}"
    )

    db_factory = ctx.get("db_factory")
    if not db_factory:
        raise RuntimeError("Arq context missing 'db_factory'")

    async with db_factory() as db:
        try:
            roadmap = await learning_service.create_roadmap(
                db=db,
                user_id=UUID(user_id),
                skill_gap_report_id=UUID(skill_gap_report_id),
            )
        except Exception as exc:
            logger.error(
                f"Failed to generate roadmap for report {skill_gap_report_id} (user {user_id}): {exc}"
            )
            return {
                "status": "failed",
                "error": f"Roadmap generation failed: {exc}",
                "skill_gap_report_id": skill_gap_report_id,
                "user_id": user_id,
            }

        items_count = len(roadmap.items) if roadmap.items else 0
        logger.info(
            f"Completed generate_roadmap job for report {skill_gap_report_id}: roadmap_id={roadmap.id}, items_count={items_count}"
        )
        return {
            "status": "complete",
            "user_id": user_id,
            "skill_gap_report_id": skill_gap_report_id,
            "roadmap_id": str(roadmap.id),
            "items_count": items_count,
        }
