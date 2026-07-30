"""
Pytest integration test suite for score_resume Arq job, ATS evaluation, grammar audit, and report API endpoints.

Run with:
    pytest tests/test_score_resume_job.py -v
"""

import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.security import ALGORITHM
from app.main import app
from app.models.logs import AiGenerationLog
from app.models.resume import Resume, ResumeReport
from app.models.user import User
from app.services import llm_service, resume_service
from app.workers.jobs.score_resume import score_resume

client = TestClient(app)


def generate_test_token(email: str = "score_test@example.com") -> str:
    """Generates a valid NextAuth JWT Bearer token."""
    payload = {"sub": email, "email": email, "name": "Test User"}
    return jwt.encode(payload, settings.nextauth_secret, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# 1. LLM Service Tests (score_resume_ats & audit_resume_grammar logging)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_score_resume_ats_and_grammar_logging():
    """Verify ATS scoring and grammar audit functions call Groq and log entries to ai_generation_logs."""
    dummy_ats = {
        "overall_score": 88,
        "formatting": 90,
        "structure": 85,
        "parseability": 90,
        "feedback": ["Great formatting"],
    }
    dummy_grammar = {
        "suggestions": [
            {
                "location": "Experience - Acme Corp",
                "issue": "Passive voice",
                "suggestion": "Managed team of 5",
            }
        ]
    }

    mock_db = AsyncMock()

    with patch("app.services.llm_service._call_groq_with_retry", AsyncMock(side_effect=[
        json.dumps(dummy_ats),
        json.dumps(dummy_grammar),
    ])):
        user_id = uuid.uuid4()
        parsed_json = {"experience": [], "education": [], "skills": {}, "achievements": []}

        ats_res = await llm_service.score_resume_ats(parsed_json, "Raw text", user_id=user_id, db=mock_db)
        grammar_res = await llm_service.audit_resume_grammar("Raw text", user_id=user_id, db=mock_db)

        assert ats_res["overall_score"] == 88
        assert len(grammar_res["suggestions"]) == 1

        # Verify two AI generation logs were saved (one for ATS, one for grammar)
        assert mock_db.add.call_count == 2
        for call in mock_db.add.call_args_list:
            log_obj = call[0][0]
            assert isinstance(log_obj, AiGenerationLog)
            assert log_obj.module == "resume"


# ---------------------------------------------------------------------------
# 2. Worker Job Null Validation & Success Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_score_resume_job_fails_when_parsed_json_is_null():
    """Verify score_resume Arq job fails cleanly if parsed_json is null (resume hasn't been parsed)."""
    resume_id = str(uuid.uuid4())
    mock_resume = Resume(
        id=UUID(resume_id),
        user_id=uuid.uuid4(),
        file_url="https://res.cloudinary.com/demo/raw/upload/resumes/unparsed.pdf",
        raw_text=None,
        parsed_json=None,  # Null parsed_json
    )

    mock_db = AsyncMock()

    class DummyAsyncSessionContext:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    ctx = {"db_factory": lambda: DummyAsyncSessionContext()}

    with patch("app.services.resume_service.get_resume_by_id", AsyncMock(return_value=mock_resume)):
        result = await score_resume(ctx, resume_id)

        assert result["status"] == "failed"
        assert "parsed_json is null" in result["error"]


@pytest.mark.asyncio
async def test_score_resume_job_success():
    """Verify score_resume Arq job succeeds for parsed resume, updates ats_score, and creates resume_reports row."""
    resume_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    mock_resume = Resume(
        id=UUID(resume_id),
        user_id=user_id,
        file_url="https://res.cloudinary.com/demo/raw/upload/resumes/resume.pdf",
        raw_text="Sample resume text",
        parsed_json={"experience": [{"company": "Acme"}]},
        ats_score=None,
    )

    mock_report = ResumeReport(
        id=uuid.uuid4(),
        resume_id=UUID(resume_id),
        job_description_id=None,
        ats_breakdown={"overall_score": 85, "formatting": 90, "structure": 80, "parseability": 85},
        grammar_suggestions=[{"location": "Summary", "issue": "Typo", "suggestion": "Fix typo"}],
        keyword_gaps=None,
        action_items=None,
    )

    mock_db = AsyncMock()

    class DummyAsyncSessionContext:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    ctx = {"db_factory": lambda: DummyAsyncSessionContext()}

    with patch("app.services.resume_service.get_resume_by_id", AsyncMock(return_value=mock_resume)), \
         patch("app.services.resume_service.create_resume_report", AsyncMock(return_value=mock_report)):

        result = await score_resume(ctx, resume_id)

        assert result["status"] == "complete"
        assert result["resume_id"] == resume_id
        assert result["report_id"] == str(mock_report.id)


# ---------------------------------------------------------------------------
# 3. API Route Tests (POST /score & GET /report)
# ---------------------------------------------------------------------------
def test_post_score_resume_route():
    """Verify POST /api/v1/resume/{id}/score enqueues score_resume job and returns job_id."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="score_test@example.com")
    dummy_resume = Resume(
        id=uuid.uuid4(),
        user_id=dummy_user.id,
        file_url="https://res.cloudinary.com/demo/raw/upload/resumes/test.pdf",
        parsed_json={"experience": []},
    )

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    with patch("app.services.resume_service.get_resume_by_id", AsyncMock(return_value=dummy_resume)), \
         patch("app.api.v1.resume._enqueue_score_job", AsyncMock(return_value="job_score_999")):

        response = client.post(f"/api/v1/resume/{dummy_resume.id}/score", headers=headers)
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == "job_score_999"
        assert data["resume_id"] == str(dummy_resume.id)

    app.dependency_overrides.clear()


def test_get_resume_report_route():
    """Verify GET /api/v1/resume/{id}/report returns the latest ResumeReport with null keyword_gaps/action_items."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="score_test@example.com")
    resume_id = uuid.uuid4()
    dummy_report = ResumeReport(
        id=uuid.uuid4(),
        resume_id=resume_id,
        job_description_id=None,
        ats_breakdown={"overall_score": 85, "formatting": 90, "structure": 80, "parseability": 85},
        grammar_suggestions=[{"location": "Header", "issue": "Minor formatting", "suggestion": "Fix font"}],
        keyword_gaps=None,
        action_items=None,
        created_at=datetime.now(),
    )

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    with patch("app.services.resume_service.get_latest_resume_report", AsyncMock(return_value=dummy_report)):
        response = client.get(f"/api/v1/resume/{resume_id}/report", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["resume_id"] == str(resume_id)
        assert data["ats_breakdown"]["overall_score"] == 85
        assert data["keyword_gaps"] is None
        assert data["action_items"] is None

    app.dependency_overrides.clear()
