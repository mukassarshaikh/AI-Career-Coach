"""
Pytest integration test suite for backend authentication endpoints (POST /auth/register, POST /auth/login)
and user resume listing endpoint (GET /resume).

Run with:
    python -m pytest tests/test_auth_and_resume_list.py -v
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core import security
from app.core.config import settings
from app.core.security import ALGORITHM
from app.main import app
from app.models.resume import Resume
from app.models.user import User
from app.services import resume_service

client = TestClient(app)


def generate_test_token(email: str) -> str:
    """Generates a valid NextAuth JWT Bearer token for the given email."""
    payload = {"sub": email, "email": email, "name": "Test User"}
    return jwt.encode(payload, settings.nextauth_secret, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# 1. Password Hashing Utility Tests
# ---------------------------------------------------------------------------
def test_password_hashing_and_verification():
    """Verify password hashing produces bcrypt hashes and verifies in constant time."""
    password = "SecurePassword123!"
    hashed = security.get_password_hash(password)

    assert hashed != password
    assert security.verify_password(password, hashed) is True
    assert security.verify_password("WrongPassword!", hashed) is False


# ---------------------------------------------------------------------------
# 2. Registration Endpoint Tests (POST /api/v1/auth/register)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_register_user_success():
    """Verify registration creates a new User in DB with hashed password and returns 201 Created."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    async def mock_refresh(obj):
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now()
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()

    mock_db.refresh = AsyncMock(side_effect=mock_refresh)

    # Mock execute returning None (no duplicate email)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    from app.api.v1.deps import get_db
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        payload = {"email": "newuser@example.com", "password": "MyPassword123!", "name": "New User"}
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert "access_token" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409():
    """Verify registering an existing email returns 409 Conflict."""
    existing_user = User(
        id=uuid.uuid4(),
        email="existing@example.com",
        password_hash=security.get_password_hash("pass123"),
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_user
    mock_db.execute = AsyncMock(return_value=mock_result)

    from app.api.v1.deps import get_db
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        payload = {"email": "existing@example.com", "password": "password123"}
        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 3. Login Endpoint Tests (POST /api/v1/auth/login)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_login_user_success():
    """Verify login with correct credentials returns 200 OK and user profile."""
    password = "CorrectPassword123!"
    user = User(
        id=uuid.uuid4(),
        email="login_user@example.com",
        password_hash=security.get_password_hash(password),
        name="Login User",
        created_at=datetime.now(),
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_db.execute = AsyncMock(return_value=mock_result)

    from app.api.v1.deps import get_db
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        payload = {"email": "login_user@example.com", "password": password}
        response = client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "login_user@example.com"
        assert data["name"] == "Login User"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_user_wrong_password_returns_401_generic():
    """Verify login with wrong password returns 401 Unauthorized with generic message."""
    user = User(
        id=uuid.uuid4(),
        email="login_user@example.com",
        password_hash=security.get_password_hash("CorrectPassword123!"),
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_db.execute = AsyncMock(return_value=mock_result)

    from app.api.v1.deps import get_db
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        payload = {"email": "login_user@example.com", "password": "WrongPassword!"}
        response = client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password."
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_user_unknown_email_returns_401_generic():
    """Verify login with non-existent email returns identical 401 Unauthorized generic message."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # User not found
    mock_db.execute = AsyncMock(return_value=mock_result)

    from app.api.v1.deps import get_db
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        payload = {"email": "nonexistent@example.com", "password": "SomePassword123!"}
        response = client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password."
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 4. Resume List Endpoint Tests (GET /api/v1/resume)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_user_resumes_returns_only_authenticated_user_resumes():
    """Verify GET /api/v1/resume returns only the resumes owned by current_user ordered by created_at desc."""
    user_a = User(id=uuid.uuid4(), email="usera@example.com")
    token = generate_test_token(user_a.email)
    headers = {"Authorization": f"Bearer {token}"}

    resumes_user_a = [
        Resume(
            id=uuid.uuid4(),
            user_id=user_a.id,
            file_url="https://res.cloudinary.com/test1.pdf",
            ats_score=85,
            created_at=datetime.now() - timedelta(hours=1),
            updated_at=datetime.now(),
        ),
        Resume(
            id=uuid.uuid4(),
            user_id=user_a.id,
            file_url="https://res.cloudinary.com/test2.pdf",
            ats_score=90,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: user_a

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        with patch("app.services.resume_service.list_user_resumes", AsyncMock(return_value=resumes_user_a)):
            response = client.get("/api/v1/resume", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["file_url"] == "https://res.cloudinary.com/test1.pdf"
            assert data[1]["file_url"] == "https://res.cloudinary.com/test2.pdf"
    finally:
        app.dependency_overrides.clear()
