"""
Health-check routes.

GET /api/v1/health          → public, no auth — confirms the backend is up
GET /api/v1/health/auth     → protected — confirms the backend is up AND the
                               frontend session token is valid
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    message: str


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Public health-check — no authentication required."""
    return HealthResponse(status="ok", message="AI Career Coach backend is running")


@router.get("/auth", response_model=HealthResponse)
async def health_check_authenticated(
    current_user: User = Depends(get_current_user),
) -> HealthResponse:
    """
    Authenticated health-check.
    Returns 200 only if the NextAuth Bearer token is valid and the
    corresponding user exists in the database.
    """
    return HealthResponse(
        status="ok",
        message=f"Authenticated as {current_user.email}",
    )
