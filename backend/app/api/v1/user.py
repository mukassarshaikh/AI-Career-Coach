"""
User management API routes — /api/v1/user/*

Endpoints:
  - DELETE /api/v1/user/me: Delete authenticated user account and all owned data (GDPR Right to Erasure).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.services import user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Delete user account and all data (GDPR Right to Erasure)",
    description="Transactional deletion of the authenticated user's account and all associated resumes, reports, skill vectors, roadmaps, chat history, and AI generation logs.",
)
async def delete_current_user_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Deletes the authenticated user account and all associated data across database tables
    and Cloudinary storage. Returns {"deleted": True}.
    """
    user_id = current_user.id
    try:
        res = await user_service.delete_user_account(db=db, user_id=user_id)
        return res
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to delete account for user {user_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to erase user account data: {str(exc)}",
        ) from exc
