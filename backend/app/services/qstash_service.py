"""
qstash_service.py — Upstash QStash publisher & signature verification service.

Handles:
  - Publishing background tasks to Upstash QStash HTTP API (no SDK dependency)
  - HMAC-SHA256 signature verification for incoming QStash webhook callbacks
  - Storing and updating job processing status in Redis
"""

import hashlib
import json
import logging
import uuid
from typing import Any, Optional
from uuid import UUID

import httpx
from jose import jwt

from app.core.config import settings
from app.core.redis_pool import get_redis_pool

logger = logging.getLogger(__name__)


async def publish_parse_resume_job(
    resume_id: UUID,
    callback_base_url: str,
) -> Optional[str]:
    """
    Publishes a parse_resume job to Upstash QStash via HTTP API.

    Returns the job_id (QStash message ID or generated ID) if QStash is configured and published.
    Returns None if QStash credentials are not configured, signaling fallback to Arq.
    """
    if not settings.qstash_url or not settings.qstash_token:
        logger.info("QStash not configured (QSTASH_URL / QSTASH_TOKEN missing); skipping QStash publish.")
        return None

    # Construct destination callback endpoint URL
    clean_base = callback_base_url.rstrip("/")
    callback_url = f"{clean_base}/api/v1/internal/jobs/parse-resume"

    # Construct QStash publish endpoint URL
    qstash_base = settings.qstash_url.rstrip("/")
    if "/v2/publish" in qstash_base:
        publish_url = f"{qstash_base}/{callback_url}"
    else:
        publish_url = f"{qstash_base}/v2/publish/{callback_url}"

    headers = {
        "Authorization": f"Bearer {settings.qstash_token}",
        "Content-Type": "application/json",
    }
    payload = {"resume_id": str(resume_id)}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                publish_url,
                json=payload,
                headers=headers,
                timeout=15.0,
            )
            response.raise_for_status()

        data = response.json()
        job_id = data.get("messageId") or f"qstash_{uuid.uuid4()}"
        logger.info(f"Successfully published parse_resume job to QStash: message_id={job_id} for resume_id={resume_id}")

        # Record initial 'queued' status in Redis
        await set_job_status(job_id=job_id, status="queued", resume_id=str(resume_id))
        return job_id

    except Exception as exc:
        logger.error(f"Failed to publish parse_resume job to QStash for resume_id={resume_id}: {exc}")
        raise RuntimeError(f"QStash enqueue failed: {exc}") from exc


def verify_qstash_signature(
    signature: str,
    body: bytes,
    destination_url: Optional[str] = None,
) -> bool:
    """
    Verifies Upstash QStash HTTP request signature (HMAC-SHA256 JWT).
    Checks both QSTASH_CURRENT_SIGNING_KEY and QSTASH_NEXT_SIGNING_KEY.

    Returns True if valid signature, False otherwise.
    """
    if not signature:
        return False

    keys = [
        k.strip()
        for k in (settings.qstash_current_signing_key, settings.qstash_next_signing_key)
        if k and k.strip()
    ]

    if not keys:
        logger.warning("No QStash signing keys configured in settings; signature verification rejected.")
        return False

    body_hash = hashlib.sha256(body).hexdigest()

    for key in keys:
        try:
            claims = jwt.decode(
                token=signature,
                key=key,
                algorithms=["HS256"],
                options={
                    "verify_sub": False,
                    "verify_iss": True,
                    "verify_exp": True,
                },
                issuer="Upstash",
            )

            # Optional body hash validation if provided in claims
            claim_body = claims.get("body")
            if claim_body and claim_body != body_hash:
                logger.warning(f"QStash signature body hash mismatch: expected {claim_body}, got {body_hash}")
                continue

            return True
        except Exception as exc:
            logger.debug(f"QStash signature verification failed for key: {exc}")
            continue

    return False


async def set_job_status(
    job_id: str,
    status: str,
    result: Optional[dict[str, Any]] = None,
    resume_id: Optional[str] = None,
) -> None:
    """
    Persists job status state into Redis for frontend polling.
    """
    try:
        redis = get_redis_pool()
        status_key = f"job_status:{job_id}"
        payload = {
            "status": status,
            "result": result,
            "resume_id": resume_id,
        }
        await redis.set(status_key, json.dumps(payload), ex=86400)  # 24h TTL

        if resume_id:
            mapping_key = f"resume_job:{resume_id}"
            await redis.set(mapping_key, job_id, ex=86400)
    except Exception as exc:
        logger.warning(f"Could not update Redis job status for job_id={job_id}: {exc}")


async def get_job_id_for_resume(resume_id: str) -> Optional[str]:
    """
    Retrieves the job_id mapped to a resume_id from Redis.
    """
    try:
        redis = get_redis_pool()
        mapping_key = f"resume_job:{resume_id}"
        val = await redis.get(mapping_key)
        if val:
            return val.decode("utf-8") if isinstance(val, bytes) else str(val)
    except Exception as exc:
        logger.warning(f"Could not fetch Redis job mapping for resume_id={resume_id}: {exc}")
    return None
