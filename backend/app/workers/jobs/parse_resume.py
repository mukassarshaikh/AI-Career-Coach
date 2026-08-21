"""
parse_resume.py — Arq worker job definition (Phase 1).

Consumes queued resume parsing jobs from Redis:
  1. Fetches the `resumes` row from Postgres by `resume_id`.
  2. Downloads the uploaded document from Cloudinary and extracts raw text.
  3. Calls Groq LLM (`llm_service.structure_resume`) to structure raw text into JSON.
  4. Logs the AI call to `ai_generation_logs` (module='resume').
  5. Updates `resumes.raw_text` and `resumes.parsed_json` in Postgres.
"""

import logging
from uuid import UUID

from app.services import llm_service, resume_service

logger = logging.getLogger(__name__)


async def parse_resume(ctx: dict, resume_id: str) -> dict:
    """
    Arq worker job that parses a resume by ID.

    Args:
        ctx: Arq context dictionary containing 'db_factory'.
        resume_id: String UUID of the resume record to process.

    Returns:
        Summary dict containing status and extracted metrics.
    """
    logger.info(f"Starting parse_resume job for resume_id={resume_id}")

    db_factory = ctx.get("db_factory")
    if not db_factory:
        raise RuntimeError("Arq context missing 'db_factory'")

    async with db_factory() as db:
        return await resume_service.process_parse_resume_job(db, UUID(resume_id))
