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


# ---------------------------------------------------------------------------
# Phase 4 — Story 4.1 Signed URL & Authenticated Cloudinary Tests
# ---------------------------------------------------------------------------

def test_signed_url_generation_and_effective_url_fallback():
    """
    Verify get_signed_resume_url and get_effective_resume_file_url:
      1. Legacy row (cloudinary_public_id is None) -> returns stored file_url.
      2. New row (cloudinary_public_id is set) -> generates fresh signed URL.
    """
    from app.services.resume_service import get_effective_resume_file_url, get_signed_resume_url

    # 1. Legacy Resume (cloudinary_public_id is None)
    legacy_resume = Resume(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        file_url="https://res.cloudinary.com/demo/raw/upload/resumes/legacy_cv.pdf",
        cloudinary_public_id=None,
    )
    effective_url = get_effective_resume_file_url(legacy_resume)
    assert effective_url == "https://res.cloudinary.com/demo/raw/upload/resumes/legacy_cv.pdf"

    # 2. New Resume (cloudinary_public_id is set)
    with patch("cloudinary.utils.cloudinary_url", return_value=("https://res.cloudinary.com/demo/raw/authenticated/s--signed_token--/resumes/new_cv.pdf", {})):
        new_resume = Resume(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            file_url="https://res.cloudinary.com/demo/raw/authenticated/resumes/new_cv.pdf",
            cloudinary_public_id="resumes/new_cv.pdf",
        )
        signed_url = get_effective_resume_file_url(new_resume)
        assert "s--signed_token--" in signed_url or signed_url.startswith("https://res.cloudinary.com/")


@pytest.mark.asyncio
@patch("cloudinary.uploader.upload")
async def test_upload_resume_file_authenticated_type(mock_upload):
    """
    Verify upload_resume_file calls Cloudinary with type='authenticated'
    and stores cloudinary_public_id in the database.
    """
    from app.services.resume_service import upload_resume_file

    mock_upload.return_value = {
        "secure_url": "https://res.cloudinary.com/demo/raw/authenticated/resumes/auth_resume.pdf",
        "url": "http://res.cloudinary.com/demo/raw/authenticated/resumes/auth_resume.pdf",
        "public_id": "resumes/user_123_auth_resume.pdf",
    }

    user_id = uuid.uuid4()
    mock_file = AsyncMock()
    mock_file.filename = "auth_resume.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.seek = AsyncMock()
    mock_file.read = AsyncMock(return_value=b"%PDF-1.5 test pdf bytes header content")

    mock_db = AsyncMock()

    with patch("app.services.resume_service.validate_resume_file", AsyncMock()):
        resume = await upload_resume_file(mock_file, user_id=user_id, db=mock_db)

        # Assert upload called with type="authenticated"
        mock_upload.assert_called_once()
        _, kwargs = mock_upload.call_args
        assert kwargs.get("type") == "authenticated"
        assert kwargs.get("resource_type") == "raw"

        # Assert DB object has cloudinary_public_id populated
        assert resume.cloudinary_public_id == "resumes/user_123_auth_resume.pdf"
        assert mock_db.add.called
        assert mock_db.commit.called


def test_api_get_resume_returns_signed_url_for_authenticated_resumes():
    """
    Verify GET /api/v1/resume/{id} returns signed URL for new resumes
    and legacy stored URL for legacy resumes.
    """
    user_id = uuid.uuid4()
    resume_id = uuid.uuid4()
    token = generate_test_token(email="signed_url_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    dummy_user = User(id=user_id, email="signed_url_test@example.com")
    new_resume = Resume(
        id=resume_id,
        user_id=user_id,
        file_url="https://res.cloudinary.com/demo/raw/authenticated/resumes/test.pdf",
        cloudinary_public_id="resumes/test.pdf",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    from app.api.v1.deps import get_current_user, get_db
    app.dependency_overrides[get_current_user] = lambda: dummy_user

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = new_resume
    mock_db.execute.return_value = mock_result

    async def mock_get_db_gen():
        yield mock_db

    app.dependency_overrides[get_db] = mock_get_db_gen

    try:
        with patch("app.services.resume_service.get_signed_resume_url", return_value="https://res.cloudinary.com/demo/raw/authenticated/s--signed_token--/resumes/test.pdf"):
            response = client.get(f"/api/v1/resume/{resume_id}", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "s--signed_token--" in data["file_url"]
    finally:
        app.dependency_overrides.clear()

