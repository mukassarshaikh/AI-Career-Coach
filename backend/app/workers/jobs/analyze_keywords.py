"""
analyze_keywords.py — Arq worker job definition (Phase 1).

Consumes queued keyword analysis jobs from Redis:
  1. Loads target JobDescription and candidate Resume records from Postgres.
  2. Fetches the candidate's prior ResumeReport (fails cleanly if no prior scoring report exists).
  3. Calls Groq LLM (`llm_service.analyze_keywords_llm`) to compare resume vs JD.
  4. Updates `job_descriptions.parsed_keywords`.
  5. Creates a NEW self-contained `resume_reports` row scoped to `job_description_id`, carrying forward
     the prior `ats_breakdown` and `grammar_suggestions` while populating `keyword_gaps` and `action_items`.
  6. Logs the AI call to `ai_generation_logs` (module='resume').
"""

import logging
from uuid import UUID

from app.services import resume_service

logger = logging.getLogger(__name__)


async def analyze_keywords(ctx: dict, job_description_id: str, resume_id: str) -> dict:
    """
    Arq worker job that analyzes keyword overlap and gaps between a resume and target job description.

    Args:
        ctx: Arq context dictionary containing 'db_factory'.
        job_description_id: String UUID of the target JobDescription record.
        resume_id: String UUID of the candidate Resume record.

    Returns:
        Summary dict containing status, resume_id, job_description_id, and report_id.
    """
    logger.info(
        f"Starting analyze_keywords job for resume_id={resume_id}, job_description_id={job_description_id}"
    )

    db_factory = ctx.get("db_factory")
    if not db_factory:
        raise RuntimeError("Arq context missing 'db_factory'")

    async with db_factory() as db:
        try:
            report = await resume_service.analyze_resume_keywords(
                db=db,
                job_description_id=UUID(job_description_id),
                resume_id=UUID(resume_id),
            )
        except Exception as exc:
            logger.error(
                f"Failed to analyze keywords for resume {resume_id} & JD {job_description_id}: {exc}"
            )
            return {"status": "failed", "error": f"Keyword analysis failed: {exc}"}

        logger.info(
            f"Completed analyze_keywords job for resume_id={resume_id}, report_id={report.id}"
        )
        return {
            "status": "complete",
            "resume_id": resume_id,
            "job_description_id": job_description_id,
            "report_id": str(report.id),
        }
