"""
Pytest integration test suite for compute_skill_gap Arq job, ivfflat migration, skill gap ranking, and API routes (POST, GET, refresh).

Run with:
    python -m pytest tests/test_compute_skill_gap_job.py -v
"""

import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.security import ALGORITHM
from app.main import app
from app.models.skill import MarketSkillReference, SkillGapReport, SkillVector
from app.models.user import User
from app.services import skill_service
from app.workers.jobs.compute_skill_gap import compute_skill_gap

client = TestClient(app)


def generate_test_token(email: str = "gap_test@example.com") -> str:
    """Generates a valid NextAuth JWT Bearer token."""
    payload = {"sub": email, "email": email, "name": "Test User"}
    return jwt.encode(payload, settings.nextauth_secret, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# 1. Migration File Check
# ---------------------------------------------------------------------------
def test_ivfflat_migration_file_exists():
    """Verify Alembic migration 0002_add_ivfflat_indexes.py exists and defines vector_cosine_ops indexes."""
    migration_path = os.path.join("alembic", "versions", "0002_add_ivfflat_indexes.py")
    assert os.path.exists(migration_path), f"Migration file missing at {migration_path}"

    with open(migration_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "ix_market_skill_reference_vector_ivfflat" in content
    assert "ix_skill_vectors_vector_ivfflat" in content
    assert "vector_cosine_ops" in content


# ---------------------------------------------------------------------------
# 2. Service & Worker Job Tests (Gap Computation & Ranking)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_compute_skill_gap_ranking_and_missing_skills():
    """Verify compute_user_skill_gap identifies missing skills and ranks them by demand_weight descending."""
    user_id = uuid.uuid4()
    vector_id = uuid.uuid4()

    mock_skill_vector = SkillVector(
        id=vector_id,
        user_id=user_id,
        vector=[0.1] * 384,
        raw_skills={"skills": ["Python", "FastAPI"]},
    )

    mock_market_refs = [
        MarketSkillReference(role_title="Backend Engineer", skill_name="Python", demand_weight=0.95),
        MarketSkillReference(role_title="Backend Engineer", skill_name="Docker", demand_weight=0.90),
        MarketSkillReference(role_title="Backend Engineer", skill_name="PostgreSQL", demand_weight=0.85),
        MarketSkillReference(role_title="Backend Engineer", skill_name="Kubernetes", demand_weight=0.75),
    ]

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    with patch("app.services.skill_service.get_skill_vector_by_user_id", AsyncMock(return_value=mock_skill_vector)):
        # Mock database query returning market references
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_market_refs
        mock_db.execute = AsyncMock(return_value=mock_result)

        report = await skill_service.compute_user_skill_gap(mock_db, user_id=user_id, target_role="Backend Engineer")

        assert isinstance(report, SkillGapReport)
        missing = report.missing_skills
        assert len(missing) == 3

        # Assert Python is NOT in missing skills (since candidate has Python)
        missing_names = [item["skill"] for item in missing]
        assert "Python" not in missing_names
        assert "Docker" in missing_names
        assert "PostgreSQL" in missing_names
        assert "Kubernetes" in missing_names

        # Assert missing skills are ordered DESCENDING by demand_weight (0.90 -> 0.85 -> 0.75)
        weights = [item["demand_weight"] for item in missing]
        assert weights == [0.90, 0.85, 0.75]
        assert mock_db.add.called
        assert mock_db.commit.called


@pytest.mark.asyncio
async def test_compute_skill_gap_job_fails_when_no_skill_vector():
    """Verify compute_skill_gap job fails cleanly if candidate has no skill vector."""
    user_id = str(uuid.uuid4())
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    class DummyAsyncSessionContext:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    ctx = {"db_factory": lambda: DummyAsyncSessionContext()}

    with patch("app.services.skill_service.get_skill_vector_by_user_id", AsyncMock(return_value=None)):
        result = await compute_skill_gap(ctx, user_id=user_id, target_role="Frontend Engineer")

        assert result["status"] == "failed"
        assert "no skill vector found" in result["error"]


# ---------------------------------------------------------------------------
# 3. API Route Tests (POST /gap-report, GET /gap-report, POST /gap-report/refresh)
# ---------------------------------------------------------------------------
def test_post_gap_report_route():
    """Verify POST /api/v1/skill/gap-report enqueues compute_skill_gap job and returns job_id."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="gap_test@example.com")
    dummy_vector = SkillVector(id=uuid.uuid4(), user_id=dummy_user.id)

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        with patch("app.services.skill_service.get_skill_vector_by_user_id", AsyncMock(return_value=dummy_vector)), \
             patch("app.api.v1.skill._enqueue_compute_gap_job", AsyncMock(return_value="job_gap_888")):

            payload = {"target_role": "Backend Engineer"}
            response = client.post("/api/v1/skill/gap-report", json=payload, headers=headers)

            assert response.status_code == 202
            data = response.json()
            assert data["target_role"] == "Backend Engineer"
            assert data["job_id"] == "job_gap_888"
    finally:
        app.dependency_overrides.clear()


def test_get_gap_report_route_returns_latest():
    """Verify GET /api/v1/skill/gap-report returns the most recent report by created_at."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="gap_test@example.com")
    vector_id = uuid.uuid4()

    latest_report = SkillGapReport(
        id=uuid.uuid4(),
        user_id=dummy_user.id,
        skill_vector_id=vector_id,
        target_role="Backend Engineer",
        missing_skills=[{"skill": "Docker", "demand_weight": 0.90, "importance": "high", "status": "missing"}],
        created_at=datetime.now(),
    )

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        with patch("app.services.skill_service.get_latest_skill_gap_report", AsyncMock(return_value=latest_report)):
            response = client.get("/api/v1/skill/gap-report", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["target_role"] == "Backend Engineer"
            assert data["missing_skills"][0]["skill"] == "Docker"
    finally:
        app.dependency_overrides.clear()


def test_post_gap_report_refresh_route_reuses_logic():
    """Verify POST /api/v1/skill/gap-report/refresh reuses the exact same enqueue logic as POST /gap-report."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="gap_test@example.com")
    dummy_vector = SkillVector(id=uuid.uuid4(), user_id=dummy_user.id)

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        with patch("app.services.skill_service.get_skill_vector_by_user_id", AsyncMock(return_value=dummy_vector)), \
             patch("app.api.v1.skill._enqueue_compute_gap_job", AsyncMock(return_value="job_gap_refresh_999")):

            payload = {"target_role": "Backend Engineer"}
            response = client.post("/api/v1/skill/gap-report/refresh", json=payload, headers=headers)

            assert response.status_code == 202
            data = response.json()
            assert data["target_role"] == "Backend Engineer"
            assert data["job_id"] == "job_gap_refresh_999"
    finally:
        app.dependency_overrides.clear()
