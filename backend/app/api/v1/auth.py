"""
Authentication API routes — /api/v1/auth/*

Endpoints:
  - POST /api/v1/auth/register: Create new user account in Postgres.
  - POST /api/v1/auth/login: Verify credentials for NextAuth authorize callback.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.core import security
from app.models.user import User
from app.schemas.auth import AuthUserResponse, LoginRequest, RegisterRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Validates email uniqueness, hashes the password using bcrypt, and creates a user record.",
)
async def register_user(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthUserResponse:
    """
    Registers a new user in Postgres. Returns 409 Conflict if email is already registered.
    """
    # 1. Check for existing user with same email
    stmt = select(User).where(User.email == body.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    # 2. Hash password with bcrypt
    hashed_password = security.get_password_hash(body.password)

    # 3. Create User record
    user = User(
        email=body.email,
        password_hash=hashed_password,
        name=body.name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"Successfully registered user {user.email} (id={user.id})")
    access_token = security.create_access_token(user.id, user.email)
    response = AuthUserResponse.model_validate(user)
    response.access_token = access_token
    return response


@router.post(
    "/login",
    response_model=AuthUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify user credentials",
    description="Verifies user email & password against stored bcrypt hash. Returns user profile & access token for NextAuth authorize callback.",
)
async def login_user(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthUserResponse:
    """
    Verifies user credentials. Returns generic 401 Unauthorized for both wrong email and wrong password.
    Returns signed access_token on success.
    """
    # Generic exception to prevent user enumeration attacks
    invalid_credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
    )

    # 1. Fetch user by email
    stmt = select(User).where(User.email == body.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise invalid_credentials_exception

    # 2. Verify password hash in constant time
    if not security.verify_password(body.password, user.password_hash):
        raise invalid_credentials_exception

    logger.info(f"Successful credentials login for user {user.email} (id={user.id})")
    access_token = security.create_access_token(user.id, user.email)
    response = AuthUserResponse.model_validate(user)
    response.access_token = access_token
    return response
