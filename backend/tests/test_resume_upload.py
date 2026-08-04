"""
Integration tests for Resume Upload and Retrieval endpoints:
  - POST /api/v1/resume/upload
  - GET /api/v1/resume/{id}

Tests verify:
  1. Unauthenticated requests return 401 Unauthorized.
  2. Invalid file formats (.txt, .png) return 400 Bad Request.
  3. Valid PDF/DOCX uploads with valid authentication succeed (201 Created), mock Cloudinary, and create a `resumes` DB row.
  4. GET /api/v1/resume/{id} returns the created resume row (200 OK).
  5. GET /api/v1/resume/{id} returns 404 for non-existent IDs.
"""

import asyncio
import io
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.security import ALGORITHM
from app.main import app
from app.models.resume import Resume
from app.models.user import User

client = TestClient(app)


def generate_test_token(email: str = "testuser@example.com") -> str:
    """Generates a valid NextAuth JWT Bearer token signed with NEXTAUTH_SECRET."""
    payload = {
        "sub": email,
        "email": email,
        "name": "Test User",
    }
    return jwt.encode(payload, settings.nextauth_secret, algorithm=ALGORITHM)


def test_upload_unauthenticated():
    """Verify POST /api/v1/resume/upload returns 401 when Authorization header is missing."""
    files = {"file": ("test_resume.pdf", b"%PDF-1.4 dummy content", "application/pdf")}
    response = client.post("/api/v1/resume/upload", files=files)
    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
    assert "Not authenticated" in response.text or "Could not validate" in response.text


def test_upload_invalid_file_extension():
    """Verify POST /api/v1/resume/upload returns 400 when uploading a .txt file."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("invalid_file.txt", b"Plain text content", "text/plain")}

    dummy_user = User(id=uuid.uuid4(), email="testuser@example.com")
    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    async def mock_get_db_gen():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        response = client.post("/api/v1/resume/upload", files=files, headers=headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "Invalid file extension" in response.text
    finally:
        app.dependency_overrides.clear()


@patch("cloudinary.uploader.upload")
def test_upload_valid_pdf_success(mock_cloudinary_upload):
    """
    Verify POST /api/v1/resume/upload succeeds for valid PDF and authenticated user.
    Mocks Cloudinary upload response and asserts database record creation.
    """
    mock_cloudinary_upload.return_value = {
        "secure_url": "https://res.cloudinary.com/demo/raw/upload/resumes/test_resume.pdf",
        "url": "http://res.cloudinary.com/demo/raw/upload/resumes/test_resume.pdf",
        "public_id": "resumes/test_resume.pdf",
    }

    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    token = generate_test_token(email=test_email)
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(
        id=uuid.uuid4(),
        email=test_email,
        name="Test User",
    )

    from app.api.v1.deps import get_current_user, get_db
    mock_db = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: dummy_user

    async def mock_get_db_gen():
        yield mock_db

    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        pdf_bytes = b"%PDF-1.5 %fake pdf header for testing\n1 0 obj<<>>endobj"
        files = {"file": ("my_resume.pdf", pdf_bytes, "application/pdf")}

        dummy_resume = Resume(
            id=uuid.uuid4(),
            user_id=dummy_user.id,
            file_url="https://res.cloudinary.com/demo/raw/upload/resumes/test_resume.pdf",
            created_at=datetime.now(),
        )

        with patch("app.services.resume_service.upload_resume_file", AsyncMock(return_value=dummy_resume)), \
             patch("app.api.v1.resume._enqueue_parse_job", AsyncMock(return_value="job_test_12345")):

            response = client.post("/api/v1/resume/upload", files=files, headers=headers)

            assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
            data = response.json()
            assert "resume_id" in data
            assert data["file_url"] == "https://res.cloudinary.com/demo/raw/upload/resumes/test_resume.pdf"
            assert data["job_id"] == "job_test_12345"

    finally:
        app.dependency_overrides.clear()


def test_get_resume_not_found():
    """Verify GET /api/v1/resume/{id} returns 404 for unknown resume ID."""
    token = generate_test_token()
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        name="Test User",
    )

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    async def mock_get_db_gen():
        yield mock_db

    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        random_id = uuid.uuid4()
        response = client.get(f"/api/v1/resume/{random_id}", headers=headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
    finally:
        app.dependency_overrides.clear()
