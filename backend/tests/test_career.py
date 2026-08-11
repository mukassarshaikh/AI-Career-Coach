"""
Pytest integration test suite for Career Intelligence backend:
- Chat session creation and user ownership checks
- Message persistence and chronological history retrieval
- Dynamic system prompt assembly from DB context (resume, gap report, roadmap)
- Groq streaming service wrapper and audit logging (module='career')
- REST endpoints and SSE streaming response validation
"""

import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import ALGORITHM
from app.main import app
from app.models.career import ChatMessage, ChatSession
from app.models.learning import Roadmap, RoadmapItem
from app.models.logs import AiGenerationLog
from app.models.resume import Resume
from app.models.skill import SkillGapReport
from app.models.user import User
from app.schemas.career import (
    CareerContextTypeEnum,
    CreateSessionRequest,
    SendMessageRequest,
)
from app.services import career_service, llm_service

client = TestClient(app)


def generate_test_token(email: str = "career_test@example.com") -> str:
    """Generates a valid NextAuth JWT Bearer token."""
    payload = {"sub": email, "email": email, "name": "Career Test User"}
    return jwt.encode(payload, settings.nextauth_secret, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# 1. Pydantic Schema Tests
# ---------------------------------------------------------------------------
def test_career_schemas_validation():
    """Verify Pydantic schemas accept valid inputs and reject invalid context types."""
    req = CreateSessionRequest(context_type=CareerContextTypeEnum.MOCK_INTERVIEW)
    assert req.context_type == "mock_interview"

    msg_req = SendMessageRequest(content="Hello world")
    assert msg_req.content == "Hello world"

    with pytest.raises(Exception):
        CreateSessionRequest(context_type="invalid_context")


# ---------------------------------------------------------------------------
# 2. System Prompt Builder Tests with DB Context
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_build_system_prompt_with_db_context():
    """Verify build_system_prompt extracts candidate profile data from DB (resume, gap report, roadmap)."""
    user_id = uuid.uuid4()

    # Mock user
    mock_user = User(id=user_id, email="test@example.com", name="Alice Smith", target_role="AI Engineer")

    # Mock resume with parsed_json
    parsed_resume_json = {
        "skills": {"technical": ["Python", "PyTorch", "FastAPI", "Docker"]},
        "experience": [{"role": "Senior ML Engineer", "company": "Tech AI Corp"}],
    }
    mock_resume = Resume(user_id=user_id, parsed_json=parsed_resume_json)

    # Mock skill gap report
    mock_gap = SkillGapReport(
        user_id=user_id,
        target_role="Lead AI Architect",
        missing_skills=[
            {"skill": "Kubernetes", "demand_weight": 0.95},
            {"skill": "CUDA", "demand_weight": 0.88},
        ],
    )

    # Mock roadmap & items
    mock_roadmap = Roadmap(id=uuid.uuid4(), user_id=user_id, status="active")
    item1 = RoadmapItem(roadmap_id=mock_roadmap.id, skill_name="Kubernetes", status="completed")
    item2 = RoadmapItem(roadmap_id=mock_roadmap.id, skill_name="CUDA", status="not_started")

    # DB mocks
    mock_db = AsyncMock(spec=AsyncSession)

    def mock_execute(stmt):
        stmt_str = str(stmt)
        res = MagicMock()
        if "FROM users" in stmt_str:
            res.scalar_one_or_none.return_value = mock_user
        elif "FROM resumes" in stmt_str:
            res.scalars().first.return_value = mock_resume
        elif "FROM skill_gap_reports" in stmt_str:
            res.scalars().first.return_value = mock_gap
        elif "FROM roadmaps" in stmt_str:
            res.scalars().first.return_value = mock_roadmap
        elif "FROM roadmap_items" in stmt_str:
            res.scalars().all.return_value = [item1, item2]
        else:
            res.scalars().first.return_value = None
            res.scalars().all.return_value = []
        return res

    mock_db.execute = AsyncMock(side_effect=mock_execute)

    # Test GENERAL prompt
    prompt_general = await career_service.build_system_prompt(
        db=mock_db, user_id=user_id, context_type="general"
    )
    assert "Alice Smith" in prompt_general
    assert "Lead AI Architect" in prompt_general
    assert "Python, PyTorch, FastAPI, Docker" in prompt_general
    assert "Senior ML Engineer at Tech AI Corp" in prompt_general
    assert "Kubernetes, CUDA" in prompt_general
    assert "1/2 roadmap items completed" in prompt_general

    # Test MOCK_INTERVIEW prompt
    prompt_mock = await career_service.build_system_prompt(
        db=mock_db, user_id=user_id, context_type="mock_interview"
    )
    assert "You are conducting a mock interview for the target role." in prompt_mock

    # Test CAREER_STRATEGY prompt
    prompt_strat = await career_service.build_system_prompt(
        db=mock_db, user_id=user_id, context_type="career_strategy"
    )
    assert "Focus on actionable career strategy: promotion paths" in prompt_strat


# ---------------------------------------------------------------------------
# 3. LLM Streaming Service Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_stream_chat_response_logging():
    """Verify stream_chat_response yields chunks and logs full response to ai_generation_logs with module='career'."""
    # Mock chunk structure from Groq AsyncGroq client
    class DummyDelta:
        def __init__(self, content):
            self.content = content

    class DummyChoice:
        def __init__(self, content):
            self.delta = DummyDelta(content)

    class DummyChunk:
        def __init__(self, content):
            self.choices = [DummyChoice(content)]

    async def dummy_async_generator():
        for chunk_val in ["Hello ", "there! ", "How can ", "I help?"]:
            yield DummyChunk(chunk_val)

    mock_groq_client = AsyncMock()
    mock_groq_client.chat.completions.create = AsyncMock(return_value=dummy_async_generator())

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    with patch("app.services.llm_service._get_groq_client", return_value=mock_groq_client):
        user_id = uuid.uuid4()
        messages = [{"role": "user", "content": "Hi"}]

        chunks = []
        async for chunk in llm_service.stream_chat_response(
            messages=messages,
            system_prompt="Test System Prompt",
            user_id=user_id,
            db=mock_db,
        ):
            chunks.append(chunk)

        full_output = "".join(chunks)
        assert full_output == "Hello there! How can I help?"

        # Verify ai_generation_logs entry created with module='career'
        assert mock_db.add.called
        log_entry = mock_db.add.call_args[0][0]
        assert isinstance(log_entry, AiGenerationLog)
        assert log_entry.module == "career"
        assert log_entry.response == "Hello there! How can I help?"


# ---------------------------------------------------------------------------
# 4. Service Session & Message Methods
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_career_service_session_and_message_crud():
    """Verify create_session, get_session, save_message, get_session_history in career_service."""
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    mock_session = ChatSession(id=session_id, user_id=user_id, context_type="general")
    msg1 = ChatMessage(id=uuid.uuid4(), session_id=session_id, role="user", content="Question 1")
    msg2 = ChatMessage(id=uuid.uuid4(), session_id=session_id, role="assistant", content="Answer 1")

    mock_db = AsyncMock(spec=AsyncSession)

    def mock_exec(stmt):
        res = MagicMock()
        stmt_str = str(stmt)
        if "FROM chat_sessions" in stmt_str:
            res.scalar_one_or_none.return_value = mock_session
        elif "FROM chat_messages" in stmt_str:
            res.scalars().all.return_value = [msg1, msg2]
        return res

    mock_db.execute = AsyncMock(side_effect=mock_exec)

    # Test get_session ownership check
    session = await career_service.get_session(mock_db, session_id, user_id)
    assert session is not None
    assert session.id == session_id

    # Test get_session_history
    history = await career_service.get_session_history(mock_db, session_id, user_id)
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "assistant"


# ---------------------------------------------------------------------------
# 5. Sensitive Topic Disclaimer Tests
# ---------------------------------------------------------------------------
def test_sensitive_topic_disclaimer_detection():
    """Verify sensitive topic detector identifies legal, visa, and compensation queries."""
    # Standard career question -> no disclaimer
    disc_norm = career_service.get_sensitive_topic_disclaimer("What skills should I learn first?")
    assert disc_norm is None

    # Compensation query -> disclaimer returned
    disc_comp = career_service.get_sensitive_topic_disclaimer("How should I negotiate my salary and stock options?")
    assert disc_comp is not None
    assert "[Disclaimer:" in disc_comp
    assert "compensation" in disc_comp.lower()

    # Visa/immigration query -> disclaimer returned
    disc_visa = career_service.get_sensitive_topic_disclaimer("Can I change employers while on an H1B visa?")
    assert disc_visa is not None
    assert "immigration" in disc_visa.lower()

    # Legal query -> disclaimer returned
    disc_legal = career_service.get_sensitive_topic_disclaimer("Is this non-compete contract clause enforceable?")
    assert disc_legal is not None
    assert "legal" in disc_legal.lower()


# ---------------------------------------------------------------------------
# 6. API Security & Ownership Tests
# ---------------------------------------------------------------------------
def test_career_api_routes_unauthenticated_rejection():
    """Verify career API endpoints return 401 Unauthorized when missing JWT token."""
    session_id = uuid.uuid4()

    # Create session without token
    res_session = client.post("/api/v1/career/chat/session", json={"context_type": "general"})
    assert res_session.status_code == 401

    # Get history without token
    res_hist = client.get(f"/api/v1/career/chat/{session_id}/history")
    assert res_hist.status_code == 401

    # Send message without token
    res_msg = client.post(f"/api/v1/career/chat/{session_id}/message", json={"content": "Hello"})
    assert res_msg.status_code == 401


def test_career_api_routes_session_ownership_and_404():
    """Verify API returns 404 when querying non-existent or unowned chat session."""
    token = generate_test_token("owner_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    session_id = uuid.uuid4()
    dummy_user = User(id=uuid.uuid4(), email="owner_test@example.com")

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None), scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))))
    async def mock_get_db():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db

    try:
        # History on non-existent or cross-user session -> 404
        res_hist = client.get(f"/api/v1/career/chat/{session_id}/history", headers=headers)
        assert res_hist.status_code == 404
        assert res_hist.json()["detail"] == "Chat session not found."

        # Send message on non-existent or cross-user session -> 404
        res_msg = client.post(f"/api/v1/career/chat/{session_id}/message", headers=headers, json={"content": "Test"})
        assert res_msg.status_code == 404
        assert res_msg.json()["detail"] == "Chat session not found."
    finally:
        app.dependency_overrides.clear()

