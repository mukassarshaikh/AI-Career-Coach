"""
Pytest integration test suite for analyze_keywords Arq job, Job Description submission, keyword gap analysis, and report resolution.

Run with:
    python -m pytest tests/test_analyze_keywords_job.py -v
"""

import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.security import ALGORITHM
from app.main import app
from app.models.logs import AiGenerationLog
from app.models.resume import JobDescription, Resume, ResumeReport
from app.models.user import User
from app.services import llm_service, resume_service
from app.workers.jobs.analyze_keywords import analyze_keywords

client = TestClient(app)


def generate_test_token(email: str = "kw_test@example.com") -> str:
    """Generates a valid NextAuth JWT Bearer token."""
    payload = {"sub": email, "email": email, "name": "Test User"}
    return jwt.encode(payload, settings.nextauth_secret, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# 1. LLM Service Tests (analyze_keywords_llm logging)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_analyze_keywords_llm_logging():
    """Verify analyze_keywords_llm calls Groq and logs entry to ai_generation_logs."""
    dummy_llm_json = {
        "matched_keywords": ["Python", "FastAPI"],
        "missing_keywords": [
            {
                "keyword": "Docker",
                "importance": "high",
                "category": "technical",
                "reason": "Required for deployment",
            }
        ],
        "action_items": [
            {
                "priority": 1,
                "section": "Skills",
                "action": "Add Docker experience",
                "impact": "Fills gap",
            }
        ],
    }

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    with patch("app.services.llm_service._call_groq_with_retry", AsyncMock(return_value=json.dumps(dummy_llm_json))):
        user_id = uuid.uuid4()
        res = await llm_service.analyze_keywords_llm(
            resume_text="Python FastAPI engineer",
            jd_text="Looking for Python, FastAPI, Docker",
            user_id=user_id,
            db=mock_db,
        )

        assert "Python" in res["matched_keywords"]
        assert res["missing_keywords"][0]["keyword"] == "Docker"

        # Verify AI generation log entry was saved
        assert mock_db.add.called
        log_obj = mock_db.add.call_args[0][0]
        assert isinstance(log_obj, AiGenerationLog)
        assert log_obj.module == "resume"


# ---------------------------------------------------------------------------
# 2. Worker Job Failure & Success Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_analyze_keywords_job_fails_when_no_prior_scoring_report():
    """Verify analyze_keywords job fails cleanly if no prior scoring report exists."""
    resume_id = str(uuid.uuid4())
    jd_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    mock_resume = Resume(
        id=UUID(resume_id),
        user_id=user_id,
        file_url="https://res.cloudinary.com/demo/raw/upload/resumes/res.pdf",
        raw_text="Resume text",
        parsed_json={"experience": []},
    )
    mock_jd = JobDescription(
        id=UUID(jd_id),
        user_id=user_id,
        resume_id=UUID(resume_id),
        raw_text="Target JD text",
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    class DummyAsyncSessionContext:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    ctx = {"db_factory": lambda: DummyAsyncSessionContext()}

    with patch("app.services.resume_service.get_resume_by_id", AsyncMock(return_value=mock_resume)), \
         patch("app.services.resume_service.get_job_description_by_id", AsyncMock(return_value=mock_jd)), \
         patch("app.services.resume_service.get_latest_resume_report", AsyncMock(return_value=None)):  # No prior report

        result = await analyze_keywords(ctx, jd_id, resume_id)

        assert result["status"] == "failed"
        assert "no prior scoring report found" in result["error"]


@pytest.mark.asyncio
async def test_analyze_keywords_job_success_data_modeling_decision():
    """
    Verify analyze_keywords job creates a NEW self-contained ResumeReport row carrying forward
    ats_breakdown and grammar_suggestions from prior report, while setting job_description_id,
    keyword_gaps, and action_items.
    """
    resume_id = str(uuid.uuid4())
    jd_id = str(uuid.uuid4())
    user_id = uuid.uuid4()

    mock_resume = Resume(
        id=UUID(resume_id),
        user_id=user_id,
        file_url="https://res.cloudinary.com/demo/raw/upload/resumes/res.pdf",
        raw_text="Resume text",
        parsed_json={"experience": []},
    )
    mock_jd = JobDescription(
        id=UUID(jd_id),
        user_id=user_id,
        resume_id=UUID(resume_id),
        raw_text="Target JD text",
    )

    prior_report = ResumeReport(
        id=uuid.uuid4(),
        resume_id=UUID(resume_id),
        job_description_id=None,
        ats_breakdown={"overall_score": 85, "formatting": 90, "structure": 80, "parseability": 85},
        grammar_suggestions=[{"location": "Header", "issue": "Typo", "suggestion": "Fix"}],
        keyword_gaps=None,
        action_items=None,
        created_at=datetime.now() - timedelta(minutes=10),
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    class DummyAsyncSessionContext:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    ctx = {"db_factory": lambda: DummyAsyncSessionContext()}

    llm_analysis_result = {
        "matched_keywords": ["Python", "FastAPI"],
        "missing_keywords": [{"keyword": "Docker", "importance": "high"}],
        "action_items": [{"priority": 1, "action": "Add Docker experience"}],
    }

    with patch("app.services.resume_service.get_resume_by_id", AsyncMock(return_value=mock_resume)), \
         patch("app.services.resume_service.get_job_description_by_id", AsyncMock(return_value=mock_jd)), \
         patch("app.services.resume_service.get_latest_resume_report", AsyncMock(return_value=prior_report)), \
         patch("app.services.llm_service.analyze_keywords_llm", AsyncMock(return_value=llm_analysis_result)):

        result = await analyze_keywords(ctx, jd_id, resume_id)

        assert result["status"] == "complete"

        # Verify a NEW ResumeReport object was added to DB
        assert mock_db.add.called
        new_report = mock_db.add.call_args[0][0]
        assert isinstance(new_report, ResumeReport)

        # DATA MODELING DECISION assertions:
        assert new_report.job_description_id == UUID(jd_id)
        assert new_report.ats_breakdown == prior_report.ats_breakdown  # Carried forward
        assert new_report.grammar_suggestions == prior_report.grammar_suggestions  # Carried forward
        assert new_report.keyword_gaps == llm_analysis_result["missing_keywords"]  # Newly populated
        assert new_report.action_items == llm_analysis_result["action_items"]  # Newly populated


# ---------------------------------------------------------------------------
# 3. API Route Tests (POST /job-description & GET /report)
# ---------------------------------------------------------------------------
def test_post_job_description_route():
    """Verify POST /api/v1/resume/{id}/job-description inserts JobDescription and returns job_id."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="kw_test@example.com")
    resume_id = uuid.uuid4()
    dummy_resume = Resume(id=resume_id, user_id=dummy_user.id, file_url="https://res.cloudinary.com/test.pdf")
    dummy_jd = JobDescription(id=uuid.uuid4(), user_id=dummy_user.id, resume_id=resume_id, raw_text="Target JD text content")

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    with patch("app.services.resume_service.get_resume_by_id", AsyncMock(return_value=dummy_resume)), \
         patch("app.services.resume_service.create_job_description", AsyncMock(return_value=dummy_jd)), \
         patch("app.api.v1.resume._enqueue_analyze_keywords_job", AsyncMock(return_value="job_kw_999")):

        payload = {"raw_text": "Target Senior Python Engineer Job Description requiring FastAPI and Docker."}
        response = client.post(f"/api/v1/resume/{resume_id}/job-description", json=payload, headers=headers)

        assert response.status_code == 202
        data = response.json()
        assert data["job_description_id"] == str(dummy_jd.id)
        assert data["resume_id"] == str(resume_id)
        assert data["job_id"] == "job_kw_999"

    app.dependency_overrides.clear()


def test_get_latest_report_returns_new_jd_report():
    """Verify GET /api/v1/resume/{id}/report returns the newly created self-contained report containing keyword_gaps."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="kw_test@example.com")
    resume_id = uuid.uuid4()
    jd_id = uuid.uuid4()

    latest_report = ResumeReport(
        id=uuid.uuid4(),
        resume_id=resume_id,
        job_description_id=jd_id,
        ats_breakdown={"overall_score": 85, "formatting": 90},
        grammar_suggestions=[{"location": "Summary", "issue": "Typo"}],
        keyword_gaps=[{"keyword": "Docker", "importance": "high"}],
        action_items=[{"priority": 1, "action": "Add Docker skill"}],
        created_at=datetime.now(),
    )

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    with patch("app.services.resume_service.get_latest_resume_report", AsyncMock(return_value=latest_report)):
        response = client.get(f"/api/v1/resume/{resume_id}/report", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["resume_id"] == str(resume_id)
        assert data["job_description_id"] == str(jd_id)
        assert data["ats_breakdown"]["overall_score"] == 85
        assert data["keyword_gaps"][0]["keyword"] == "Docker"
        assert data["action_items"][0]["priority"] == 1

    app.dependency_overrides.clear()
