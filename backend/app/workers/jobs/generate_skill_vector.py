"""
generate_skill_vector.py — Arq worker job definition (Phase 1).

Consumes queued skill vector generation jobs from Redis:
  1. Fetches candidate Resume record from Postgres.
  2. Validates that `parsed_json` is populated (fails cleanly if null).
  3. Extracts skills list from `parsed_json`.
  4. Generates a 384-dim embedding vector via `embedding_service`.
  5. Upserts the `skill_vectors` row for the user in Postgres.
"""

import logging
from uuid import UUID

from app.services import resume_service, skill_service

logger = logging.getLogger(__name__)


async def generate_skill_vector(ctx: dict, resume_id: str) -> dict:
    """
    Arq worker job that generates a 384-dim skill vector for a parsed resume.

    Args:
        ctx: Arq context dictionary containing 'db_factory'.
        resume_id: String UUID of the candidate Resume record.

    Returns:
        Summary dict containing status, resume_id, user_id, vector_id, and skills_count.
    """
    logger.info(f"Starting generate_skill_vector job for resume_id={resume_id}")

    db_factory = ctx.get("db_factory")
    if not db_factory:
        raise RuntimeError("Arq context missing 'db_factory'")

    async with db_factory() as db:
        # 1. Load candidate resume
        uuid_obj = UUID(resume_id)
        resume = await resume_service.get_resume_by_id(db, resume_id=uuid_obj)
        if not resume:
            logger.error(f"Resume {resume_id} not found in database.")
            return {"status": "failed", "error": "Resume record not found"}

        # 2. Validate parsed_json is populated
        if not resume.parsed_json:
            logger.error(f"Resume {resume_id} has null parsed_json; cannot generate skill vector.")
            return {
                "status": "failed",
                "error": "Cannot generate skill vector: parsed_json is null. Resume must be parsed first.",
            }

        # 3. Upsert user's skill vector record
        try:
            skill_vector = await skill_service.upsert_user_skill_vector(db, resume)
        except Exception as exc:
            logger.error(f"Failed to generate skill vector for resume {resume_id}: {exc}")
            return {"status": "failed", "error": f"Skill vector generation failed: {exc}"}

        skills_count = len(skill_vector.raw_skills.get("skills", [])) if skill_vector.raw_skills else 0
        logger.info(
            f"Completed generate_skill_vector job for resume_id={resume_id}, user_id={resume.user_id}, skills_count={skills_count}"
        )
        return {
            "status": "complete",
            "resume_id": resume_id,
            "user_id": str(resume.user_id),
            "vector_id": str(skill_vector.id),
            "skills_count": skills_count,
        }
