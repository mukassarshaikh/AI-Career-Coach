"""
JWT validation for NextAuth session tokens.

NextAuth (with the CredentialsProvider) signs a JWT using NEXTAUTH_SECRET.
We decode that token here using the same secret so the backend can
independently verify every authenticated request.
"""

from datetime import datetime
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.core.config import settings

ALGORITHM = "HS256"


def decode_nextauth_token(token: str) -> dict:
    """
    Decode and validate a NextAuth JWT.
    Returns the decoded payload on success, raises HTTPException on failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.nextauth_secret,
            algorithms=[ALGORITHM],
            options={"verify_aud": False},  # NextAuth doesn't set aud by default
        )
        email: Optional[str] = payload.get("email") or payload.get("sub")
        if email is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


def get_email_from_token(token: str) -> str:
    payload = decode_nextauth_token(token)
    email = payload.get("email") or payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing email/sub claim",
        )
    return email
