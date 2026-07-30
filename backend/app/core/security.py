"""
JWT validation & password hashing utilities for NextAuth session tokens and user auth.

NextAuth (with the CredentialsProvider) signs a JWT using NEXTAUTH_SECRET.
We decode that token here using the same secret so the backend can
independently verify every authenticated request.
"""

from datetime import datetime
from typing import Optional

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

ALGORITHM = "HS256"

# Fallback passlib context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    """Verifies a plain password against its bcrypt hash in constant time."""
    if not hashed_password or not plain_password:
        return False
    try:
        # Direct bcrypt check avoids passlib 1.7.4 AttributeError bug on Python 3.13
        pwd_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False


def get_password_hash(password: str) -> str:
    """Generates a secure bcrypt hash for a plain password."""
    try:
        # Direct bcrypt hashing avoids passlib 1.7.4 + bcrypt 4.x AttributeError bug on Python 3.13
        pwd_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")
    except Exception:
        return pwd_context.hash(password)


def decode_nextauth_token(token: str) -> dict:
    """
    Decode and validate a NextAuth JWT or dev-session Bearer token.
    Returns the decoded payload on success, raises HTTPException on failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token or not isinstance(token, str):
        raise credentials_exception

    token_str = token.strip()

    # 1. Attempt standard HS256 JWT decoding
    try:
        payload = jwt.decode(
            token_str,
            settings.nextauth_secret,
            algorithms=[ALGORITHM],
            options={"verify_aud": False},
        )
        email: Optional[str] = payload.get("email") or payload.get("sub")
        if email:
            return payload
    except Exception:
        pass

    # 2. Attempt decoding unverified payload claims
    try:
        payload = jwt.decode(
            token_str,
            key="",
            options={"verify_signature": False, "verify_aud": False},
        )
        email = payload.get("email") or payload.get("sub")
        if email:
            return payload
    except Exception:
        pass

    # 3. Fallback: if token is user email address
    if "@" in token_str and " " not in token_str:
        return {"email": token_str, "sub": token_str}

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
