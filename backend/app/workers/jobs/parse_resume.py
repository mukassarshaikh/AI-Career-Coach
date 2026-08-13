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
        # 1. Fetch resume row
        uuid_obj = UUID(resume_id)
        resume = await resume_service.get_resume_by_id(db, resume_id=uuid_obj)
        if not resume:
            logger.error(f"Resume {resume_id} not found in database.")
            raise RuntimeError(f"Resume {resume_id} not found in database.")

        # 2. Extract text from Cloudinary file URL (uses fresh signed URL for authenticated resumes, legacy URL for legacy rows)
        effective_url = resume_service.get_effective_resume_file_url(resume)
        raw_text = await resume_service.extract_text_from_url(effective_url)

        # 3. Call Groq LLM to structure resume data into JSON — same principle:
        # let a genuine LLM failure fail the job rather than saving an empty
        # parsed_json that looks like a real (but empty) result to the user.
        parsed_json = await llm_service.structure_resume(
            text=raw_text,
            user_id=resume.user_id,
            db=db,
        )

        # 4. Save results to resumes table
        resume.raw_text = raw_text
        resume.parsed_json = parsed_json
        await db.commit()

        logger.info(f"Completed parse_resume job for resume_id={resume_id}")
        return {
            "status": "complete",
            "resume_id": resume_id,
            "raw_text_length": len(raw_text),
            "parsed": True,
        }
