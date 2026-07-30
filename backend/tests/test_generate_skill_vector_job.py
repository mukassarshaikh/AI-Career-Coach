"""
Pytest integration test suite for generate_skill_vector Arq job, skill extraction, 384-dim embedding generation, single-user upserting, and API route.

Run with:
    pytest tests/test_generate_skill_vector_job.py -v
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.security import ALGORITHM
from app.main import app
from app.models.resume import Resume
from app.models.skill import SkillVector
from app.models.user import User
from app.services import embedding_service, skill_service
from app.workers.jobs.generate_skill_vector import generate_skill_vector

client = TestClient(app)


def generate_test_token(email: str = "vector_test@example.com") -> str:
    """Generates a valid NextAuth JWT Bearer token."""
    payload = {"sub": email, "email": email, "name": "Test User"}
    return jwt.encode(payload, settings.nextauth_secret, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# 1. Skill Extraction & Embedding Generation Tests
# ---------------------------------------------------------------------------
def test_extract_skills_from_parsed_json():
    """Verify extract_skills_from_parsed_json pulls technical, tools, and soft_skills."""
    parsed_json = {
        "experience": [],
        "education": [],
        "skills": {
            "technical": ["Python", "FastAPI", "PostgreSQL"],
            "tools": ["Docker", "Git"],
            "soft_skills": ["Leadership", "Problem Solving"],
        },
    }
    extracted = skill_service.extract_skills_from_parsed_json(parsed_json)
    assert "Python" in extracted
    assert "FastAPI" in extracted
    assert "Docker" in extracted
    assert "Leadership" in extracted
    assert len(extracted) == 7


def test_generate_embedding_dimension():
    """Verify embedding_service returns a list of floats with exact dimension 384."""
    text = "Candidate competencies and skills: Python, FastAPI, PostgreSQL, Docker"
    vector = embedding_service.generate_embedding(text)

    assert isinstance(vector, list)
    assert len(vector) == 384
    assert all(isinstance(val, float) for val in vector)


# ---------------------------------------------------------------------------
# 2. Worker Job Null Validation & Single-User Upsert Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_skill_vector_job_fails_when_parsed_json_is_null():
    """Verify generate_skill_vector Arq job fails cleanly if parsed_json is null."""
    resume_id = str(uuid.uuid4())
    mock_resume = Resume(
        id=uuid.UUID(resume_id),
        user_id=uuid.uuid4(),
        file_url="https://res.cloudinary.com/demo/raw/upload/resumes/unparsed.pdf",
        parsed_json=None,
    )

    mock_db = AsyncMock()

    class DummyAsyncSessionContext:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    ctx = {"db_factory": lambda: DummyAsyncSessionContext()}

    with patch("app.services.resume_service.get_resume_by_id", AsyncMock(return_value=mock_resume)):
        result = await generate_skill_vector(ctx, resume_id)

        assert result["status"] == "failed"
        assert "parsed_json is null" in result["error"]


@pytest.mark.asyncio
async def test_generate_skill_vector_upsert_behavior():
    """Verify upsert_user_skill_vector updates existing user record instead of creating duplicate rows."""
    user_id = uuid.uuid4()
    resume_id = uuid.uuid4()

    mock_resume = Resume(
        id=resume_id,
        user_id=user_id,
        file_url="https://res.cloudinary.com/demo/raw/upload/resumes/res.pdf",
        parsed_json={
            "skills": {
                "technical": ["Python", "PostgreSQL"],
                "tools": ["Git"],
                "soft_skills": [],
            }
        },
    )

    existing_vector = SkillVector(
        id=uuid.uuid4(),
        user_id=user_id,
        resume_id=uuid.uuid4(),  # Old resume ID
        vector=[0.1] * 384,
        raw_skills={"skills": ["Python"]},
    )

    mock_db = AsyncMock()

    with patch("app.services.skill_service.get_skill_vector_by_user_id", AsyncMock(return_value=existing_vector)), \
         patch("app.services.embedding_service.generate_embedding", return_value=[0.5] * 384):

        updated_vector = await skill_service.upsert_user_skill_vector(mock_db, mock_resume)

        # Assert same object ID is reused (updated in place)
        assert updated_vector.id == existing_vector.id
        assert updated_vector.resume_id == resume_id
        assert updated_vector.vector[0] == 0.5
        assert "PostgreSQL" in updated_vector.raw_skills["skills"]
        assert mock_db.commit.called


# ---------------------------------------------------------------------------
# 3. API Route Tests (POST /api/v1/skill/vector)
# ---------------------------------------------------------------------------
def test_post_skill_vector_route():
    """Verify POST /api/v1/skill/vector enqueues generate_skill_vector job and returns job_id."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="vector_test@example.com")
    resume_id = uuid.uuid4()
    dummy_resume = Resume(id=resume_id, user_id=dummy_user.id, parsed_json={"skills": {}})

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    with patch("app.services.resume_service.get_resume_by_id", AsyncMock(return_value=dummy_resume)), \
         patch("app.api.v1.skill._enqueue_skill_vector_job", AsyncMock(return_value="job_vector_777")):

        payload = {"resume_id": str(resume_id)}
        response = client.post("/api/v1/skill/vector", json=payload, headers=headers)

        assert response.status_code == 202
        data = response.json()
        assert data["resume_id"] == str(resume_id)
        assert data["job_id"] == "job_vector_777"

    app.dependency_overrides.clear()
