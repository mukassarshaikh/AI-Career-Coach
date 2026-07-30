"""
score_resume.py — Arq worker job definition (Phase 1).

Consumes queued resume scoring jobs from Redis:
  1. Fetches the `resumes` row from Postgres by `resume_id`.
  2. Validates that `parsed_json` is populated (fails cleanly if null).
  3. Calls Groq LLM to compute ATS score breakdown and audit grammar.
  4. Updates `resumes.ats_score` and creates a `resume_reports` database row.
  5. Logs both AI calls to `ai_generation_logs` (module='resume').
"""

import logging
from uuid import UUID

from app.services import resume_service

logger = logging.getLogger(__name__)


async def score_resume(ctx: dict, resume_id: str) -> dict:
    """
    Arq worker job that scores a parsed resume by ID.

    Args:
        ctx: Arq context dictionary containing 'db_factory'.
        resume_id: String UUID of the resume record to score.

    Returns:
        Summary dict containing status, ats_score, and report_id.
    """
    logger.info(f"Starting score_resume job for resume_id={resume_id}")

    db_factory = ctx.get("db_factory")
    if not db_factory:
        raise RuntimeError("Arq context missing 'db_factory'")

    async with db_factory() as db:
        # 1. Fetch resume row
        uuid_obj = UUID(resume_id)
        resume = await resume_service.get_resume_by_id(db, resume_id=uuid_obj)
        if not resume:
            logger.error(f"Resume {resume_id} not found in database.")
            return {"status": "failed", "error": "Resume record not found"}

        # 2. Check if parsed_json is populated
        if not resume.parsed_json:
            logger.error(f"Resume {resume_id} has null parsed_json; cannot score.")
            return {
                "status": "failed",
                "error": "Cannot score resume: parsed_json is null. Resume must be parsed first.",
            }

        # 3. Create evaluation report & update ats_score
        try:
            report = await resume_service.create_resume_report(db, resume)
        except Exception as exc:
            logger.error(f"Failed to score resume {resume_id}: {exc}")
            return {"status": "failed", "error": f"Scoring evaluation failed: {exc}"}

        logger.info(
            f"Completed score_resume job for resume_id={resume_id}, ats_score={resume.ats_score}"
        )
        return {
            "status": "complete",
            "resume_id": resume_id,
            "ats_score": resume.ats_score,
            "report_id": str(report.id),
        }
