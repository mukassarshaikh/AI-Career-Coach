"""
test_qstash_parse_resume.py — Focused tests for QStash parse_resume publisher, signature verification, internal callback, idempotency, and status transitions.
"""

import hashlib
import json
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.main import app
from app.models.resume import Resume
from app.models.user import User
from app.services import qstash_service, resume_service

client = TestClient(app)


def generate_qstash_jwt_signature(
    body: bytes,
    secret: str,
    issuer: str = "Upstash",
    sub: str = "http://testserver/api/v1/internal/jobs/parse-resume",
) -> str:
    """Helper to generate a valid QStash HMAC-SHA256 signature token."""
    body_hash = hashlib.sha256(body).hexdigest()
    now = int(time.time())
    payload = {
        "iss": issuer,
        "sub": sub,
        "exp": now + 300,
        "nbf": now - 30,
        "body": body_hash,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


# ---------------------------------------------------------------------------
# 1. QStash Publisher Tests (Request, Authorization Header, Payload)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_qstash_publish_request_headers_and_payload(monkeypatch):
    """
    Verifies QStash publish sends correct Authorization header, target URL,
    and JSON payload containing only resume_id.
    """
    test_url = "https://qstash.upstash.io/v2/publish"
    test_token = "qstash_secret_token_abc123"
    resume_id = uuid.uuid4()
    callback_base = "https://ai-career-coach-f5dg.onrender.com"

    monkeypatch.setattr(settings, "qstash_url", test_url)
    monkeypatch.setattr(settings, "qstash_token", test_token)

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"messageId": "msg_qstash_9999"}

    captured_url = None
    captured_headers = None
    captured_json = None

    async def mock_post(url, json, headers, timeout):
        nonlocal captured_url, captured_headers, captured_json
        captured_url = url
        captured_headers = headers
        captured_json = json
        return mock_response

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post.side_effect = mock_post

    with patch("httpx.AsyncClient", return_value=mock_client), \
         patch("app.services.qstash_service.set_job_status", AsyncMock()):

        job_id = await qstash_service.publish_parse_resume_job(
            resume_id=resume_id,
            callback_base_url=callback_base,
        )

        assert job_id == "msg_qstash_9999"
        assert captured_url == "https://qstash.upstash.io/v2/publish/https://ai-career-coach-f5dg.onrender.com/api/v1/internal/jobs/parse-resume"
        assert captured_headers["Authorization"] == "Bearer qstash_secret_token_abc123"
        assert captured_headers["Content-Type"] == "application/json"
        assert captured_json == {"resume_id": str(resume_id)}


# ---------------------------------------------------------------------------
# 2. Signature Verification Tests (Accept Valid & Reject Invalid)
# ---------------------------------------------------------------------------
def test_verify_qstash_signature_accept_and_reject(monkeypatch):
    """
    Verifies that valid QStash JWT signatures pass verification while invalid
    or forged signatures are rejected.
    """
    current_key = "sig_key_current_12345"
    next_key = "sig_key_next_67890"

    monkeypatch.setattr(settings, "qstash_current_signing_key", current_key)
    monkeypatch.setattr(settings, "qstash_next_signing_key", next_key)

    body = json.dumps({"resume_id": str(uuid.uuid4())}).encode("utf-8")

    # Valid signature using current key
    valid_sig = generate_qstash_jwt_signature(body, current_key)
    assert qstash_service.verify_qstash_signature(valid_sig, body) is True

    # Valid signature using next key
    valid_next_sig = generate_qstash_jwt_signature(body, next_key)
    assert qstash_service.verify_qstash_signature(valid_next_sig, body) is True

    # Invalid signature (wrong key)
    invalid_sig = generate_qstash_jwt_signature(body, "wrong_secret_key")
    assert qstash_service.verify_qstash_signature(invalid_sig, body) is False

    # Forged body (modified payload body)
    tampered_body = json.dumps({"resume_id": str(uuid.uuid4())}).encode("utf-8")
    assert qstash_service.verify_qstash_signature(valid_sig, tampered_body) is False


def test_callback_rejects_invalid_signature(monkeypatch):
    """
    Verifies POST /api/v1/internal/jobs/parse-resume returns 401 Unauthorized
    when given an invalid or missing QStash signature.
    """
    monkeypatch.setattr(settings, "qstash_current_signing_key", "valid_secret_key")

    payload = {"resume_id": str(uuid.uuid4())}
    headers = {"Upstash-Signature": "invalid.jwt.token"}

    response = client.post("/api/v1/internal/jobs/parse-resume", json=payload, headers=headers)
    assert response.status_code == 401
    assert "signature" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 3. Callback Execution & Trigger Parse Logic
# ---------------------------------------------------------------------------
def test_callback_accepts_valid_signature_and_triggers_parse_logic(monkeypatch):
    """
    Verifies POST /api/v1/internal/jobs/parse-resume accepts valid signature
    and triggers the shared parse_resume business logic.
    """
    signing_key = "test_signing_key_secret"
    monkeypatch.setattr(settings, "qstash_current_signing_key", signing_key)

    resume_id = uuid.uuid4()
    dummy_resume = Resume(
        id=resume_id,
        user_id=uuid.uuid4(),
        file_url="https://res.cloudinary.com/demo/raw/authenticated/resume.pdf",
        raw_text=None,
        parsed_json=None,
    )

    body_bytes = json.dumps({"resume_id": str(resume_id)}).encode("utf-8")
    valid_sig = generate_qstash_jwt_signature(body_bytes, signing_key)

    from app.api.v1.deps import get_db
    mock_db = AsyncMock()

    async def mock_get_db_gen():
        yield mock_db

    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        with patch("app.services.resume_service.get_resume_by_id", AsyncMock(return_value=dummy_resume)), \
             patch("app.services.resume_service.process_parse_resume_job", AsyncMock(return_value={"status": "complete", "resume_id": str(resume_id)})) as mock_process, \
             patch("app.services.qstash_service.set_job_status", AsyncMock()) as mock_set_status, \
             patch("app.services.qstash_service.get_redis_pool", MagicMock()):

            headers = {"Upstash-Signature": valid_sig, "Content-Type": "application/json"}
            response = client.post("/api/v1/internal/jobs/parse-resume", data=body_bytes, headers=headers)

            assert response.status_code == 200
            assert response.json()["status"] == "complete"
            mock_process.assert_called_once_with(mock_db, resume_id=resume_id)
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 4. Callback Idempotency Tests
# ---------------------------------------------------------------------------
def test_callback_is_idempotent_when_already_parsed(monkeypatch):
    """
    Verifies duplicate callback delivery for an already parsed resume returns 200 OK
    immediately without re-parsing or calling LLM.
    """
    signing_key = "test_signing_key_secret"
    monkeypatch.setattr(settings, "qstash_current_signing_key", signing_key)

    resume_id = uuid.uuid4()
    dummy_parsed_resume = Resume(
        id=resume_id,
        user_id=uuid.uuid4(),
        file_url="https://res.cloudinary.com/demo/raw/authenticated/resume.pdf",
        raw_text="Extracted text",
        parsed_json={"skills": ["Python"]},
    )

    body_bytes = json.dumps({"resume_id": str(resume_id)}).encode("utf-8")
    valid_sig = generate_qstash_jwt_signature(body_bytes, signing_key)

    from app.api.v1.deps import get_db
    mock_db = AsyncMock()

    async def mock_get_db_gen():
        yield mock_db

    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        with patch("app.services.resume_service.get_resume_by_id", AsyncMock(return_value=dummy_parsed_resume)), \
             patch("app.services.resume_service.process_parse_resume_job", AsyncMock()) as mock_process:

            headers = {"Upstash-Signature": valid_sig, "Content-Type": "application/json"}
            response = client.post("/api/v1/internal/jobs/parse-resume", data=body_bytes, headers=headers)

            assert response.status_code == 200
            assert response.json()["status"] == "complete"
            assert "already parsed" in response.json()["message"].lower()
            # Must NOT call process_parse_resume_job again
            mock_process.assert_not_called()
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 5. Job Status Transitions & Integration Flow Test
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_job_status_transitions_queued_to_in_progress_to_complete(monkeypatch):
    """
    Verifies state machine transitions: queued -> in_progress -> complete in Redis.
    """
    job_id = f"msg_{uuid.uuid4()}"
    resume_id = str(uuid.uuid4())

    redis_store = {}

    mock_redis = AsyncMock()

    async def mock_set(key, val, ex=None, nx=False):
        if nx and key in redis_store:
            return None
        redis_store[key] = val
        return True

    async def mock_get(key):
        val = redis_store.get(key)
        return val.encode("utf-8") if isinstance(val, str) else val

    mock_redis.set = AsyncMock(side_effect=mock_set)
    mock_redis.get = AsyncMock(side_effect=mock_get)

    with patch("app.services.qstash_service.get_redis_pool", return_value=mock_redis):

        # 1. Enqueue / Publish state -> queued
        await qstash_service.set_job_status(job_id=job_id, status="queued", resume_id=resume_id)
        cached_queued = json.loads((await mock_redis.get(f"job_status:{job_id}")).decode("utf-8"))
        assert cached_queued["status"] == "queued"

        # 2. Callback starts -> in_progress
        await qstash_service.set_job_status(job_id=job_id, status="in_progress", resume_id=resume_id)
        cached_progress = json.loads((await mock_redis.get(f"job_status:{job_id}")).decode("utf-8"))
        assert cached_progress["status"] == "in_progress"

        # 3. Callback completes -> complete
        result_data = {"status": "complete", "parsed": True}
        await qstash_service.set_job_status(job_id=job_id, status="complete", result=result_data, resume_id=resume_id)
        cached_complete = json.loads((await mock_redis.get(f"job_status:{job_id}")).decode("utf-8"))
        assert cached_complete["status"] == "complete"
        assert cached_complete["result"] == result_data
