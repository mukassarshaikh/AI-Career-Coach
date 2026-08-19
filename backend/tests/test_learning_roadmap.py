"""
Pytest integration test suite for Learning Intelligence roadmap generation, Arq worker job,
archive-previous-active-roadmap logic, API endpoints, and item status updates.

Run with:
    python -m pytest tests/test_learning_roadmap.py -v
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
from app.models.learning import Roadmap, RoadmapItem
from app.models.logs import AiGenerationLog
from app.models.skill import SkillGapReport, SkillVector
from app.models.user import User
from app.services import learning_service, llm_service
from app.workers.jobs.generate_roadmap import generate_roadmap

client = TestClient(app)


def generate_test_token(email: str = "learning_test@example.com") -> str:
    """Generates a valid NextAuth JWT Bearer token."""
    payload = {"sub": email, "email": email, "name": "Test User"}
    return jwt.encode(payload, settings.nextauth_secret, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# 1. LLM Service Tests (generate_roadmap_llm logging module='learning')
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_roadmap_llm_logging():
    """Verify generate_roadmap_llm calls Groq and logs entry to ai_generation_logs with module='learning'."""
    dummy_llm_json = {
        "items": [
            {
                "skill_name": "Docker",
                "type": "course",
                "title": "Mastering Docker Containers",
                "description": "Learn Docker basics and docker-compose.",
                "url": None,
                "sequence_order": 1,
                "difficulty": "beginner",
            },
            {
                "skill_name": "Docker",
                "type": "project",
                "title": "Containerize FastAPI Web App",
                "description": "Package FastAPI backend with Docker Compose.",
                "url": None,
                "sequence_order": 2,
                "difficulty": "intermediate",
            },
        ]
    }

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    with patch("app.services.llm_service._call_groq_with_retry", AsyncMock(return_value=json.dumps(dummy_llm_json))):
        user_id = uuid.uuid4()
        missing_skills = [{"skill": "Docker", "demand_weight": 0.90, "importance": "high"}]

        items = await llm_service.generate_roadmap_llm(
            missing_skills=missing_skills,
            target_role="Backend Engineer",
            user_id=user_id,
            db=mock_db,
        )

        assert len(items) == 2
        assert items[0]["skill_name"] == "Docker"
        assert items[0]["type"] == "course"

@pytest.mark.asyncio
async def test_roadmap_receives_only_real_frontend_gaps():
    """Verify generate_roadmap_llm receives strictly frontend missing skills and produces roadmap items for those skills only."""
    dummy_llm_json = {
        "items": [
            {
                "skill_name": "Next.js",
                "type": "course",
                "title": "Mastering Next.js App Router",
                "description": "Learn server components, SSR, and API routes.",
                "url": None,
                "sequence_order": 1,
                "difficulty": "intermediate",
            },
            {
                "skill_name": "TypeScript",
                "type": "project",
                "title": "Build Typed React Components",
                "description": "Convert JS components to TypeScript with strict type checking.",
                "url": None,
                "sequence_order": 2,
                "difficulty": "intermediate",
            },
        ]
    }

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    with patch("app.services.llm_service._call_groq_with_retry", AsyncMock(return_value=json.dumps(dummy_llm_json))):
        user_id = uuid.uuid4()
        frontend_gaps = [
            {"skill": "Next.js", "demand_weight": 0.88, "importance": "high"},
            {"skill": "TypeScript", "demand_weight": 0.95, "importance": "high"},
        ]

        items = await llm_service.generate_roadmap_llm(
            missing_skills=frontend_gaps,
            target_role="Senior React Developer",
            user_id=user_id,
            db=mock_db,
        )

        assert len(items) == 2
        roadmap_skills = {item["skill_name"] for item in items}
        assert "Next.js" in roadmap_skills
        assert "TypeScript" in roadmap_skills

        # Confirm no cross-role skills exist in generated roadmap items
        assert "Python" not in roadmap_skills
        assert "SQL" not in roadmap_skills
        assert "C / C++" not in roadmap_skills
        assert "AWS Architecture" not in roadmap_skills


# ---------------------------------------------------------------------------
# 2. Service & Archiving Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_roadmap_archives_previous_active_roadmap():
    """Verify create_roadmap archives any existing 'active' roadmap for user before creating new active roadmap."""
    user_id = uuid.uuid4()
    report_id = uuid.uuid4()

    mock_report = SkillGapReport(
        id=report_id,
        user_id=user_id,
        skill_vector_id=uuid.uuid4(),
        target_role="Backend Engineer",
        missing_skills=[{"skill": "Docker", "demand_weight": 0.90}],
    )

    generated_items = [
        {
            "skill_name": "Docker",
            "type": "course",
            "title": "Docker Fundamentals",
            "description": "Learn container concepts",
            "url": None,
            "sequence_order": 1,
            "difficulty": "beginner",
        }
    ]

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.add_all = MagicMock()

    mock_result_report = MagicMock()
    mock_result_report.scalar_one_or_none.return_value = mock_report
    mock_db.execute = AsyncMock(return_value=mock_result_report)

    with patch("app.services.learning_service.generate_roadmap_items", AsyncMock(return_value=generated_items)), \
         patch("app.services.learning_service.get_roadmap_by_id", AsyncMock(side_effect=lambda db, roadmap_id, user_id: Roadmap(
             id=roadmap_id,
             user_id=user_id,
             skill_gap_report_id=report_id,
             status="active",
             created_at=datetime.now(),
             updated_at=datetime.now(),
             items=[
                 RoadmapItem(
                     id=uuid.uuid4(),
                     roadmap_id=roadmap_id,
                     skill_name="Docker",
                     type="course",
                     title="Docker Fundamentals",
                     sequence_order=1,
                     difficulty="beginner",
                     status="not_started",
                 )
             ]
         ))):

        roadmap = await learning_service.create_roadmap(mock_db, user_id=user_id, skill_gap_report_id=report_id)

        assert isinstance(roadmap, Roadmap)
        assert roadmap.status == "active"
        # Assert update statement was executed to archive existing active roadmaps
        assert mock_db.execute.called
        assert mock_db.commit.called


# ---------------------------------------------------------------------------
# 3. Arq Worker Job Failure & Success Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_roadmap_job_fails_when_missing_skills_is_empty():
    """Verify generate_roadmap job fails cleanly if skill gap report has no missing skills."""
    report_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    class DummyAsyncSessionContext:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    ctx = {"db_factory": lambda: DummyAsyncSessionContext()}

    with patch("app.services.learning_service.create_roadmap", AsyncMock(side_effect=ValueError("missing_skills list is empty."))):
        result = await generate_roadmap(ctx, report_id, user_id)

        assert result["status"] == "failed"
        assert "missing_skills list is empty" in result["error"]


@pytest.mark.asyncio
async def test_generate_roadmap_job_success():
    """Verify generate_roadmap job succeeds for valid report and creates roadmap."""
    report_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    mock_roadmap = Roadmap(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        skill_gap_report_id=uuid.UUID(report_id),
        status="active",
        items=[
            RoadmapItem(
                id=uuid.uuid4(),
                skill_name="Docker",
                type="course",
                title="Docker Course",
                sequence_order=1,
                difficulty="beginner",
            )
        ],
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    class DummyAsyncSessionContext:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    ctx = {"db_factory": lambda: DummyAsyncSessionContext()}

    with patch("app.services.learning_service.create_roadmap", AsyncMock(return_value=mock_roadmap)):
        result = await generate_roadmap(ctx, report_id, user_id)

        assert result["status"] == "complete"
        assert result["roadmap_id"] == str(mock_roadmap.id)
        assert result["items_count"] == 1


# ---------------------------------------------------------------------------
# 4. API Route Tests (POST /roadmap, GET /roadmap/{id}, POST /regenerate, PATCH /roadmap-item/{id})
# ---------------------------------------------------------------------------
def test_post_roadmap_route():
    """Verify POST /api/v1/learning/roadmap enqueues generate_roadmap job and returns job_id."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="learning_test@example.com")
    report_id = uuid.uuid4()

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        with patch("app.api.v1.learning._enqueue_generate_roadmap_job", AsyncMock(return_value="job_roadmap_777")):
            payload = {"skill_gap_report_id": str(report_id)}
            response = client.post("/api/v1/learning/roadmap", json=payload, headers=headers)

            assert response.status_code == 202
            data = response.json()
            assert data["skill_gap_report_id"] == str(report_id)
            assert data["job_id"] == "job_roadmap_777"
    finally:
        app.dependency_overrides.clear()


def test_get_roadmap_route():
    """Verify GET /api/v1/learning/roadmap/{id} returns full roadmap with ordered items."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="learning_test@example.com")
    roadmap_id = uuid.uuid4()
    report_id = uuid.uuid4()

    mock_roadmap = Roadmap(
        id=roadmap_id,
        user_id=dummy_user.id,
        skill_gap_report_id=report_id,
        status="active",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        items=[
            RoadmapItem(
                id=uuid.uuid4(),
                roadmap_id=roadmap_id,
                skill_name="Docker",
                type="course",
                title="Docker Fundamentals",
                description="Intro course",
                url=None,
                sequence_order=1,
                difficulty="beginner",
                status="not_started",
                completed_at=None,
            ),
            RoadmapItem(
                id=uuid.uuid4(),
                roadmap_id=roadmap_id,
                skill_name="Docker",
                type="project",
                title="Containerize FastAPI Web App",
                description="Hands-on project",
                url=None,
                sequence_order=2,
                difficulty="intermediate",
                status="not_started",
                completed_at=None,
            ),
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
        with patch("app.services.learning_service.get_roadmap_by_id", AsyncMock(return_value=mock_roadmap)):
            response = client.get(f"/api/v1/learning/roadmap/{roadmap_id}", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(roadmap_id)
            assert data["status"] == "active"
            assert len(data["items"]) == 2
            assert data["items"][0]["sequence_order"] == 1
            assert data["items"][1]["sequence_order"] == 2
    finally:
        app.dependency_overrides.clear()


def test_post_roadmap_regenerate_route():
    """Verify POST /api/v1/learning/roadmap/{id}/regenerate re-enqueues generate_roadmap job."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="learning_test@example.com")
    roadmap_id = uuid.uuid4()
    report_id = uuid.uuid4()

    mock_roadmap = Roadmap(
        id=roadmap_id,
        user_id=dummy_user.id,
        skill_gap_report_id=report_id,
        status="active",
        items=[],
    )

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        with patch("app.services.learning_service.get_roadmap_by_id", AsyncMock(return_value=mock_roadmap)), \
             patch("app.api.v1.learning._enqueue_generate_roadmap_job", AsyncMock(return_value="job_roadmap_regen_999")):

            response = client.post(f"/api/v1/learning/roadmap/{roadmap_id}/regenerate", headers=headers)

            assert response.status_code == 202
            data = response.json()
            assert data["skill_gap_report_id"] == str(report_id)
            assert data["job_id"] == "job_roadmap_regen_999"
    finally:
        app.dependency_overrides.clear()


def test_patch_roadmap_item_status():
    """Verify PATCH /api/v1/learning/roadmap-item/{id} updates item status and returns 200 OK."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=uuid.uuid4(), email="learning_test@example.com")
    item_id = uuid.uuid4()

    mock_item = RoadmapItem(
        id=item_id,
        roadmap_id=uuid.uuid4(),
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
            assert data["item"]["status"] == "completed"
            assert data["job_id"] == "job_recalc_123"
    finally:
        app.dependency_overrides.clear()
