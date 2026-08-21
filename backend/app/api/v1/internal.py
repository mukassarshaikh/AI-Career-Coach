"""
Internal callback routes for QStash webhook execution — /api/v1/internal/*

Endpoints:
  - POST /api/v1/internal/jobs/parse-resume: QStash webhook callback to parse resume.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.core.redis_pool import get_redis_pool
from app.services import qstash_service, resume_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/jobs", tags=["internal-jobs"])


class ParseResumeCallbackPayload(BaseModel):
    resume_id: UUID


@router.post(
    "/parse-resume",
    status_code=status.HTTP_200_OK,
    summary="QStash callback for parse_resume background job",
    description="Internal authenticated webhook endpoint called by Upstash QStash to execute resume parsing.",
)
async def qstash_parse_resume_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Validates QStash signature, checks job idempotency, updates job status,
    and executes shared resume parsing logic.
    """
    raw_body = await request.body()
    signature = request.headers.get("Upstash-Signature") or request.headers.get("upstash-signature") or ""

    # 1. Signature Verification
    is_valid = qstash_service.verify_qstash_signature(
        signature=signature,
        body=raw_body,
        destination_url=str(request.url),
    )
    if not is_valid:
        logger.warning(f"Rejected unauthenticated QStash callback attempt to {request.url}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing QStash signature.",
        )

    # 2. Parse Payload
    try:
        payload = ParseResumeCallbackPayload.model_validate_json(raw_body)
    except Exception as exc:
        logger.error(f"Invalid JSON payload received in QStash callback: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body payload.",
        ) from exc

    resume_id = payload.resume_id

    # 3. Fetch Resume Record & Idempotency Checks
    resume = await resume_service.get_resume_by_id(db, resume_id=resume_id)
    if not resume:
        logger.error(f"Resume record {resume_id} not found during QStash callback execution.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume record not found.",
        )

    # Idempotency Check A: If already parsed, return success immediately
    if resume.parsed_json is not None:
        logger.info(f"QStash callback for resume {resume_id}: already parsed. Idempotent return.")
        job_id = await qstash_service.get_job_id_for_resume(str(resume_id))
        if job_id:
            await qstash_service.set_job_status(
                job_id=job_id,
                status="complete",
                result={"status": "complete", "resume_id": str(resume_id), "parsed": True},
                resume_id=str(resume_id),
            )
        return {"status": "complete", "message": "Resume is already parsed."}

    # Idempotency Check B: Concurrency lock via Redis
    lock_acquired = True
    lock_key = f"job_lock:{resume_id}"
    try:
        redis = get_redis_pool()
        acquired = await redis.set(lock_key, "locked", nx=True, ex=300)
        lock_acquired = bool(acquired)
    except Exception as exc:
        logger.warning(f"Redis concurrency check failed for resume {resume_id}: {exc}")

    if not lock_acquired:
        logger.info(f"QStash callback for resume {resume_id}: job currently in progress in another worker.")
        return {"status": "in_progress", "message": "Resume parsing is already in progress."}

    # Fetch mapped job_id for Redis status updates
    job_id = await qstash_service.get_job_id_for_resume(str(resume_id))
    if not job_id:
        job_id = f"qstash_exec_{resume_id}"

    # 4. Mark status as 'in_progress'
    await qstash_service.set_job_status(
        job_id=job_id,
        status="in_progress",
        resume_id=str(resume_id),
    )

    # 5. Execute Parsing Logic
    try:
        result = await resume_service.process_parse_resume_job(db, resume_id=resume_id)
        await qstash_service.set_job_status(
            job_id=job_id,
            status="complete",
            result=result,
            resume_id=str(resume_id),
        )
        logger.info(f"QStash callback successfully completed parse_resume for resume_id={resume_id}")
        return result
    except Exception as exc:
        logger.error(f"Error executing parse_resume in QStash callback for resume_id={resume_id}: {exc}")
        safe_error = "Failed to process resume document. Please verify file format and try again."
        await qstash_service.set_job_status(
            job_id=job_id,
            status="failed",
            result={"error": safe_error},
            resume_id=str(resume_id),
        )
        # Release concurrency lock on failure
        try:
            redis = get_redis_pool()
            await redis.delete(lock_key)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=safe_error,
        ) from exc
