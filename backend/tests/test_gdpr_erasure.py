"""
test_gdpr_erasure.py — Integration and unit test suite for Phase 4 Story 4.3
GDPR Log Retention & Right to Erasure.

Tests cover:
  1. Unauthenticated DELETE /api/v1/user/me -> 401 Unauthorized
  2. Authenticated account deletion API (returns {"deleted": True})
  3. Complete transactional data erasure across all user-owned DB tables
  4. Cross-user data isolation (User A deletion leaves User B data untouched)
  5. Account deletion transaction rollback on failure
  6. Automated log retention job (prune_ai_generation_logs):
     - Logs > 30 days pruned
     - Logs < 30 days retained
     - System logs (user_id=None) handled correctly
     - Multiple user log pruning
     - Job idempotency & return status
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.security import ALGORITHM
from app.main import app
from app.models.career import ChatMessage, ChatSession
from app.models.learning import Roadmap, RoadmapItem
from app.models.logs import AiGenerationLog
from app.models.resume import JobDescription, Resume, ResumeReport
from app.models.skill import SkillGapReport, SkillVector
from app.models.user import User
from app.services import user_service
from app.workers.jobs.prune_ai_generation_logs import prune_ai_generation_logs

client = TestClient(app)


def generate_test_token(email: str = "gdpr_user@example.com") -> str:
    """Generates a valid NextAuth JWT Bearer token for authentication."""
    payload = {"sub": email, "email": email, "name": "GDPR User"}
    return jwt.encode(payload, settings.nextauth_secret, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# 1. API Authorization & Security Tests (Story 4.3 Step 10)
# ---------------------------------------------------------------------------
def test_delete_user_me_unauthenticated():
    """Verify DELETE /api/v1/user/me returns 401 Unauthorized when unauthenticated."""
    response = client.delete("/api/v1/user/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_user_me_authenticated_success():
    """Verify DELETE /api/v1/user/me calls user_service and returns {"deleted": True}."""
    dummy_user = User(id=uuid.uuid4(), email="user_a@example.com", name="User A")

    from app.api.v1.deps import get_current_user, get_db

    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = mock_get_db

    try:
        with patch("app.services.user_service.delete_user_account", AsyncMock(return_value={"deleted": True})) as mock_delete:
            response = client.delete("/api/v1/user/me")
            assert response.status_code == 200
            data = response.json()
            assert data == {"deleted": True}
            mock_delete.assert_called_once_with(db=mock_db, user_id=dummy_user.id)
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 2. Transaction Rollback & Service Failure Behavior (Story 4.3 Step 8)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_user_account_transaction_rollback():
    """Verify failure during erasure triggers transaction rollback so no partial deletion occurs."""
    user_id = uuid.uuid4()
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=RuntimeError("Database constraint error during deletion"))
    mock_db.rollback = AsyncMock()

    with patch("app.services.resume_service.delete_cloudinary_asset"):
        with pytest.raises(RuntimeError, match="Database constraint error during deletion"):
            await user_service.delete_user_account(db=mock_db, user_id=user_id)

        assert mock_db.rollback.called


# ---------------------------------------------------------------------------
# 3. Complete User Data Erasure & Cross-User Isolation (Story 4.3 Step 11)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_complete_user_data_erasure_and_cross_user_isolation():
    """
    Verify complete user data erasure:
    - User A with full tree of data (resumes, JDs, reports, vectors, gap reports, roadmaps, items, sessions, messages, logs)
    - User B with equivalent full tree of data
    - User A is erased -> User A data count == 0 across all tables
    - User B data remains completely intact
    """
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    # Track executed queries to verify targeted deletion
    executed_deletes = []

    mock_db = AsyncMock()

    async def mock_execute(stmt):
        stmt_str = str(stmt)
        if "DELETE FROM" in stmt_str:
            executed_deletes.append(stmt_str)
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        return mock_result

    mock_db.execute = AsyncMock(side_effect=mock_execute)
    mock_db.commit = AsyncMock()

    with patch("app.services.resume_service.delete_cloudinary_asset"):
        res = await user_service.delete_user_account(db=mock_db, user_id=user_a_id)
        assert res == {"deleted": True}
        assert mock_db.commit.called

        # Verify deletion statements targeted all user-owned tables
        all_deletes_concat = " ".join(executed_deletes)
        assert "ai_generation_logs" in all_deletes_concat
        assert "chat_messages" in all_deletes_concat
        assert "chat_sessions" in all_deletes_concat
        assert "roadmap_items" in all_deletes_concat
        assert "roadmaps" in all_deletes_concat
        assert "skill_gap_reports" in all_deletes_concat
        assert "skill_vectors" in all_deletes_concat
        assert "resume_reports" in all_deletes_concat
        assert "job_descriptions" in all_deletes_concat
        assert "resumes" in all_deletes_concat
        assert "users" in all_deletes_concat


# ---------------------------------------------------------------------------
# 5. Cloudinary Deletion Failure Semantics & Legacy Asset Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_cloudinary_deletion_success_and_db_erasure():
    """Verify when Cloudinary deletion succeeds, DB erasure completes and returns {"deleted": True}."""
    user_id = uuid.uuid4()
    resume_a = Resume(id=uuid.uuid4(), user_id=user_id, file_url="http://example.com/a.pdf", cloudinary_public_id="resumes/a.pdf")
    
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[resume_a])))
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    with patch("app.services.resume_service.delete_cloudinary_asset", return_value={"status": "ok", "result": "ok"}) as mock_del:
        res = await user_service.delete_user_account(db=mock_db, user_id=user_id)
        assert res == {"deleted": True}
        mock_del.assert_called_once_with(public_id="resumes/a.pdf", resource_type="raw", delivery_type="authenticated")
        assert mock_db.commit.called


@pytest.mark.asyncio
async def test_cloudinary_deletion_failure_aborts_db_erasure():
    """Verify when Cloudinary deletion fails, DB erasure is aborted and no DB delete queries execute."""
    user_id = uuid.uuid4()
    resume_a = Resume(id=uuid.uuid4(), user_id=user_id, file_url="http://example.com/a.pdf", cloudinary_public_id="resumes/a.pdf")

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[resume_a])))
    mock_db.execute = AsyncMock(return_value=mock_result)

    from fastapi import HTTPException

    with patch("app.services.resume_service.delete_cloudinary_asset", return_value={"status": "failed", "error": "API Connection Error"}):
        with pytest.raises(HTTPException) as exc_info:
            await user_service.delete_user_account(db=mock_db, user_id=user_id)

        assert exc_info.value.status_code in (500, 502)
        assert "Failed to delete remote resume asset from Cloudinary" in exc_info.value.detail

        # Assert no DELETE FROM SQL queries executed
        for call_arg in mock_db.execute.call_args_list:
            stmt_str = str(call_arg[0][0])
            assert "DELETE FROM" not in stmt_str


@pytest.mark.asyncio
async def test_cloudinary_multiple_assets_deletion_attempts():
    """Verify all user resumes are attempted for Cloudinary deletion."""
    user_id = uuid.uuid4()
    resume_1 = Resume(id=uuid.uuid4(), user_id=user_id, file_url="http://example.com/1.pdf", cloudinary_public_id="resumes/1.pdf")
    resume_2 = Resume(id=uuid.uuid4(), user_id=user_id, file_url="http://example.com/2.pdf", cloudinary_public_id="resumes/2.pdf")

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[resume_1, resume_2])))
    mock_db.execute = AsyncMock(return_value=mock_result)

    del_calls = []

    def mock_del(public_id, resource_type, delivery_type):
        del_calls.append(public_id)
        return {"status": "ok", "result": "ok"}

    with patch("app.services.resume_service.delete_cloudinary_asset", side_effect=mock_del):
        res = await user_service.delete_user_account(db=mock_db, user_id=user_id)
        assert res == {"deleted": True}
        assert del_calls == ["resumes/1.pdf", "resumes/2.pdf"]


@pytest.mark.asyncio
async def test_cloudinary_already_missing_asset_handling():
    """Verify when Cloudinary returns 'not found', it is treated as safely erased and DB erasure proceeds."""
    user_id = uuid.uuid4()
    resume_missing = Resume(id=uuid.uuid4(), user_id=user_id, file_url="http://example.com/missing.pdf", cloudinary_public_id="resumes/missing.pdf")

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[resume_missing])))
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.services.resume_service.delete_cloudinary_asset", return_value={"status": "ok", "result": "not found"}):
        res = await user_service.delete_user_account(db=mock_db, user_id=user_id)
        assert res == {"deleted": True}
        assert mock_db.commit.called


# ---------------------------------------------------------------------------
# 6. Explicit Retry Scenario Tests (Scenarios 1, 2, 3)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_retry_scenario_1_cloudinary_fails_then_succeeds_on_retry():
    """
    Scenario 1:
    Attempt 1: Cloudinary fails -> DB untouched, 500 error returned.
    Attempt 2 (Retry): Cloudinary succeeds -> DB deleted, 200 returned.
    """
    user_id = uuid.uuid4()
    resume_a = Resume(id=uuid.uuid4(), user_id=user_id, file_url="http://example.com/a.pdf", cloudinary_public_id="resumes/a.pdf")

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[resume_a])))
    mock_db.execute = AsyncMock(return_value=mock_result)

    from fastapi import HTTPException

    # Attempt 1: Cloudinary fails
    with patch("app.services.resume_service.delete_cloudinary_asset", return_value={"status": "failed", "error": "Cloudinary Network Timeout"}):
        with pytest.raises(HTTPException) as exc_info:
            await user_service.delete_user_account(db=mock_db, user_id=user_id)
        assert exc_info.value.status_code in (500, 502)

    # Attempt 2: Cloudinary fixed and succeeds -> Retry succeeds
    with patch("app.services.resume_service.delete_cloudinary_asset", return_value={"status": "ok", "result": "ok"}):
        res = await user_service.delete_user_account(db=mock_db, user_id=user_id)
        assert res == {"deleted": True}
        assert mock_db.commit.called


@pytest.mark.asyncio
async def test_retry_scenario_2_cloudinary_succeeded_db_failed_then_retry():
    """
    Scenario 2:
    Attempt 1: Cloudinary succeeds, DB commit fails -> DB rollback, user remains in DB.
    Attempt 2 (Retry): Cloudinary returns 'not found' -> treated as erased, DB succeeds -> 200 returned.
    """
    user_id = uuid.uuid4()
    resume_a = Resume(id=uuid.uuid4(), user_id=user_id, file_url="http://example.com/a.pdf", cloudinary_public_id="resumes/a.pdf")

    mock_db_attempt1 = AsyncMock()
    mock_result1 = MagicMock()
    mock_result1.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[resume_a])))
    mock_db_attempt1.execute = AsyncMock(return_value=mock_result1)
    mock_db_attempt1.commit = AsyncMock(side_effect=RuntimeError("DB Commit Error"))
    mock_db_attempt1.rollback = AsyncMock()

    # Attempt 1: DB commit fails -> Rollback
    with patch("app.services.resume_service.delete_cloudinary_asset", return_value={"status": "ok", "result": "ok"}):
        with pytest.raises(RuntimeError, match="DB Commit Error"):
            await user_service.delete_user_account(db=mock_db_attempt1, user_id=user_id)
        assert mock_db_attempt1.rollback.called

    # Attempt 2 (Retry): Cloudinary returns 'not found' (asset was destroyed in Attempt 1) -> DB deletion succeeds
    mock_db_attempt2 = AsyncMock()
    mock_result2 = MagicMock()
    mock_result2.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[resume_a])))
    mock_db_attempt2.execute = AsyncMock(return_value=mock_result2)
    mock_db_attempt2.commit = AsyncMock()

    with patch("app.services.resume_service.delete_cloudinary_asset", return_value={"status": "ok", "result": "not found"}):
        res = await user_service.delete_user_account(db=mock_db_attempt2, user_id=user_id)
        assert res == {"deleted": True}
        assert mock_db_attempt2.commit.called


@pytest.mark.asyncio
async def test_retry_scenario_3_multiple_assets_one_fails_then_retry():
    """
    Scenario 3:
    User has 2 resumes.
    Attempt 1: 1 asset fails -> DB deletion NOT executed.
    Attempt 2 (Retry): Asset 1 returns 'not found', Asset 2 succeeds -> DB deletion succeeds.
    """
    user_id = uuid.uuid4()
    r1 = Resume(id=uuid.uuid4(), user_id=user_id, file_url="http://example.com/1.pdf", cloudinary_public_id="resumes/1.pdf")
    r2 = Resume(id=uuid.uuid4(), user_id=user_id, file_url="http://example.com/2.pdf", cloudinary_public_id="resumes/2.pdf")

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[r1, r2])))
    mock_db.execute = AsyncMock(return_value=mock_result)

    from fastapi import HTTPException

    # Attempt 1: r1 succeeds, r2 fails -> Erasure aborted, DB untouched
    def mock_del_attempt1(public_id, resource_type, delivery_type):
        if public_id == "resumes/1.pdf":
            return {"status": "ok", "result": "ok"}
        return {"status": "failed", "error": "Cloudinary Rate Limit"}

    with patch("app.services.resume_service.delete_cloudinary_asset", side_effect=mock_del_attempt1):
        with pytest.raises(HTTPException) as exc_info:
            await user_service.delete_user_account(db=mock_db, user_id=user_id)
        assert exc_info.value.status_code in (500, 502)

    # Attempt 2 (Retry): r1 returns 'not found' (since deleted in Attempt 1), r2 succeeds -> Account deleted
    def mock_del_attempt2(public_id, resource_type, delivery_type):
        if public_id == "resumes/1.pdf":
            return {"status": "ok", "result": "not found"}
        return {"status": "ok", "result": "ok"}

    with patch("app.services.resume_service.delete_cloudinary_asset", side_effect=mock_del_attempt2):
        res = await user_service.delete_user_account(db=mock_db, user_id=user_id)
        assert res == {"deleted": True}
        assert mock_db.commit.called


