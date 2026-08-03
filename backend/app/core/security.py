"""
JWT validation & password hashing utilities for NextAuth session tokens and user auth.

NextAuth (with the CredentialsProvider) signs a JWT using NEXTAUTH_SECRET.
We decode that token here using the same secret so the backend can
independently verify every authenticated request.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

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


def create_access_token(
    user_id: UUID,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Mints a backend-issued HS256 JWT access token with sub, email, iat, and exp claims.
    Default lifetime is 24 hours.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(to_encode, settings.nextauth_secret, algorithm=ALGORITHM)


def decode_nextauth_token(token: str) -> dict:
    """
    Strictly decode and validate a backend-issued HS256 Bearer JWT.
    Verifies signature and expiration using settings.nextauth_secret.
    Raises HTTPException(401) on any failure — NO fallbacks.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired session token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token or not isinstance(token, str):
        raise credentials_exception

    token_str = token.strip()

    try:
        payload = jwt.decode(
            token_str,
            settings.nextauth_secret,
            algorithms=[ALGORITHM],
            options={"verify_aud": False, "verify_signature": True, "verify_exp": True},
        )
        email: Optional[str] = payload.get("email") or payload.get("sub")
        if not email:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception
    except Exception:
        raise credentials_exception


def get_email_from_token(token: str) -> str:
    payload = decode_nextauth_token(token)
    email = payload.get("email") or payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return email

