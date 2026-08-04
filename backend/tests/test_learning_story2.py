"""
Pytest integration test suite for Phase 2 Story 2:
  - PATCH /api/v1/learning/roadmap-item/{id} (status update, completed_at, ownership check)
  - GET /api/v1/learning/roadmap (active roadmap without ID)
  - recalculate_skill_vector Arq background worker job
  - GET /api/v1/dashboard/summary (roadmap completion metrics)

Run with:
    python -m pytest tests/test_learning_story2.py -v
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.security import ALGORITHM
from app.main import app
from app.models.learning import Roadmap, RoadmapItem
from app.models.resume import Resume
from app.models.skill import SkillGapReport, SkillVector
from app.models.user import User
from app.services import learning_service
from app.workers.jobs.recalculate_skill_vector import recalculate_skill_vector

client = TestClient(app)


def generate_test_token(email: str = "story2_test@example.com") -> str:
    """Generates a valid NextAuth JWT Bearer token."""
    payload = {"sub": email, "email": email, "name": "Test User"}
    return jwt.encode(payload, settings.nextauth_secret, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# 1. PATCH /roadmap-item/{id} Status Update & Security Tests
# ---------------------------------------------------------------------------
def test_update_roadmap_item_status_completed_enqueues_recalc():
    """Verify PATCH /learning/roadmap-item/{id} with status='completed' updates status, sets completed_at, and enqueues recalculation."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="story2_test@example.com")
    item_id = uuid.uuid4()
    roadmap_id = uuid.uuid4()

    mock_item = RoadmapItem(
        id=item_id,
        roadmap_id=roadmap_id,
        skill_name="Docker",
        type="course",
        title="Docker Fundamentals",
        sequence_order=1,
        difficulty="beginner",
        status="completed",
        completed_at=datetime.now(),
    )

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        with patch("app.services.learning_service.update_roadmap_item_status", AsyncMock(return_value=(mock_item, "Backend Engineer"))), \
             patch("app.api.v1.learning._enqueue_recalculate_skill_vector_job", AsyncMock(return_value="job_recalc_123")):

            payload = {"status": "completed"}
            response = client.patch(f"/api/v1/learning/roadmap-item/{item_id}", json=payload, headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["item"]["id"] == str(item_id)
            assert data["item"]["status"] == "completed"
            assert data["item"]["completed_at"] is not None
            assert data["job_id"] == "job_recalc_123"
            assert "background skill vector recalculation enqueued" in data["message"]
    finally:
        app.dependency_overrides.clear()


def test_update_roadmap_item_status_in_progress_no_job():
    """Verify PATCH /learning/roadmap-item/{id} with status='in_progress' does NOT enqueue recalculation job."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="story2_test@example.com")
    item_id = uuid.uuid4()

    mock_item = RoadmapItem(
        id=item_id,
        roadmap_id=uuid.uuid4(),
        skill_name="Docker",
        type="course",
        title="Docker Fundamentals",
        sequence_order=1,
        difficulty="beginner",
        status="in_progress",
        completed_at=None,
    )

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        with patch("app.services.learning_service.update_roadmap_item_status", AsyncMock(return_value=(mock_item, "Backend Engineer"))):
            payload = {"status": "in_progress"}
            response = client.patch(f"/api/v1/learning/roadmap-item/{item_id}", json=payload, headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["item"]["status"] == "in_progress"
            assert data["item"]["completed_at"] is None
            assert data["job_id"] is None
    finally:
        app.dependency_overrides.clear()


def test_update_roadmap_item_ownership_check_returns_404():
    """Verify attempting to PATCH an item owned by another user (or non-existent) returns 404 Not Found."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="story2_test@example.com")

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        # Service returns None due to ownership check failure
        with patch("app.services.learning_service.update_roadmap_item_status", AsyncMock(return_value=None)):
            foreign_item_id = uuid.uuid4()
            payload = {"status": "completed"}
            response = client.patch(f"/api/v1/learning/roadmap-item/{foreign_item_id}", json=payload, headers=headers)

            assert response.status_code == 404
            assert response.json()["detail"] == "Roadmap item not found."
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 2. GET /learning/roadmap (Active Roadmap Retrieval) Tests
# ---------------------------------------------------------------------------
def test_get_active_roadmap_route_success():
    """Verify GET /api/v1/learning/roadmap returns current active roadmap for authenticated user."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="story2_test@example.com")
    roadmap_id = uuid.uuid4()

    mock_roadmap = Roadmap(
        id=roadmap_id,
        user_id=dummy_user.id,
        skill_gap_report_id=uuid.uuid4(),
        status="active",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        items=[
            RoadmapItem(
                id=uuid.uuid4(),
                roadmap_id=roadmap_id,
                skill_name="FastAPI",
                type="course",
                title="FastAPI Mastery",
                sequence_order=1,
                difficulty="intermediate",
                status="not_started",
            )
        ],
    )

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        with patch("app.services.learning_service.get_active_roadmap_by_user_id", AsyncMock(return_value=mock_roadmap)):
            response = client.get("/api/v1/learning/roadmap", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(roadmap_id)
            assert data["status"] == "active"
            assert len(data["items"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_get_active_roadmap_route_404_when_none():
    """Verify GET /api/v1/learning/roadmap returns 404 with clear message when user has no active roadmap."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="story2_test@example.com")
    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        with patch("app.services.learning_service.get_active_roadmap_by_user_id", AsyncMock(return_value=None)):
            response = client.get("/api/v1/learning/roadmap", headers=headers)

            assert response.status_code == 404
            assert response.json()["detail"] == "No active roadmap found. Generate one from your skill gap report."
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 3. recalculate_skill_vector Worker Job Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_recalculate_skill_vector_worker_job_success():
    """Verify recalculate_skill_vector job re-embeds skills and computes new skill gap report."""
    user_id = str(uuid.uuid4())
    resume_id = uuid.uuid4()
    target_role = "Backend Engineer"

    mock_resume = Resume(
        id=resume_id,
        user_id=uuid.UUID(user_id),
        file_url="https://res.cloudinary.com/test.pdf",
        parsed_json={"skills": {"technical": ["Python", "FastAPI"]}},
    )

    mock_vector = SkillVector(id=uuid.uuid4(), user_id=uuid.UUID(user_id))
    mock_report = SkillGapReport(id=uuid.uuid4(), user_id=uuid.UUID(user_id), target_role=target_role)

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    # Mock DB query execution returning candidate resume
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_resume
    mock_db.execute = AsyncMock(return_value=mock_res)

    class DummyAsyncSessionContext:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    ctx = {"db_factory": lambda: DummyAsyncSessionContext()}

    with patch("app.services.skill_service.upsert_user_skill_vector", AsyncMock(return_value=mock_vector)), \
         patch("app.services.skill_service.compute_user_skill_gap", AsyncMock(return_value=mock_report)):

        result = await recalculate_skill_vector(ctx, user_id, target_role)

        assert result["status"] == "complete"
        assert result["user_id"] == user_id
        assert result["target_role"] == target_role
        assert result["new_skill_gap_report_id"] == str(mock_report.id)


# ---------------------------------------------------------------------------
# 4. GET /dashboard/summary Endpoint Tests
# ---------------------------------------------------------------------------
def test_get_dashboard_summary_route():
    """Verify GET /api/v1/dashboard/summary returns consolidated metrics including roadmap progress."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="story2_test@example.com")
    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    from app.schemas.dashboard import DashboardSummaryResponse
    summary_data = DashboardSummaryResponse(
        resume_score=85,
        missing_skills_count=3,
        target_role="Backend Engineer",
        roadmap_total_items=4,
        roadmap_completed_items=1,
        roadmap_completion_percentage=25.0,
        active_roadmap_id=uuid.uuid4(),
    )

    try:
        with patch("app.services.dashboard_service.get_user_dashboard_summary", AsyncMock(return_value=summary_data)):
            response = client.get("/api/v1/dashboard/summary", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["resume_score"] == 85
            assert data["missing_skills_count"] == 3
            assert data["roadmap_total_items"] == 4
            assert data["roadmap_completed_items"] == 1
            assert data["roadmap_completion_percentage"] == 25.0
            assert data["active_roadmap_id"] is not None
    finally:
        app.dependency_overrides.clear()
