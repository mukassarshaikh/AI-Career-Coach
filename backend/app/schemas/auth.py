"""
Auth Pydantic schemas for request/response serialization.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request payload for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
    name: Optional[str] = Field(None, description="User full name")


class LoginRequest(BaseModel):
    """Request payload for credentials authentication."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class AuthUserResponse(BaseModel):
    """Response returned upon successful registration or login for NextAuth."""

    id: UUID
    email: str
    name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
