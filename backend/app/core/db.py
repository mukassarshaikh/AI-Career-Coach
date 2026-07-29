"""
SQLAlchemy async engine + session factory.

Engine is created lazily on first access so the app module can be imported
without a valid DATABASE_URL (useful for CLI tools, testing, etc.).

The DATABASE_URL is normalised to always use postgresql+asyncpg:// and strip/translate
libpq-specific query parameters (such as sslmode and channel_binding) into asyncpg-compatible formats.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy models."""
    pass


# Parameters supported by libpq/psycopg2 drivers but NOT accepted by asyncpg's connect() method.
# Passing these to asyncpg via SQLAlchemy causes TypeError: connect() got an unexpected keyword argument '...'
UNSUPPORTED_LIBPQ_PARAMS: set[str] = {
    "channel_binding",
    "gssencmode",
    "krbsrvname",
    "target_session_attrs",
    "service",
    "passfile",
    "sslcert",
    "sslkey",
    "sslrootcert",
    "sslcrl",
}


def normalise_url(url: str) -> str:
    """
    Normalises a PostgreSQL connection URL for compatibility with SQLAlchemy + asyncpg.

    Neon (and other cloud Postgres providers) supply libpq-formatted URLs containing
    parameters like `sslmode=require` and `channel_binding=require`.

    `asyncpg` does not accept these libpq query parameters directly:
      - `sslmode` is translated to `ssl` (e.g., `sslmode=require` -> `ssl=require`).
      - Unsupported parameters (`channel_binding`, `gssencmode`, etc.) are stripped.
      - Schemes `postgresql://` and `postgres://` are normalized to `postgresql+asyncpg://`.

    Args:
        url: Raw database URL (e.g., from environment variables).

    Returns:
        Cleaned, asyncpg-compatible connection URL string.
    """
    if not url:
        return url

    parsed = urlparse(url)

    # 1. Normalize scheme for asyncpg dialect
    scheme = parsed.scheme
    if scheme in ("postgresql", "postgres"):
        scheme = "postgresql+asyncpg"

    # 2. Parse and transform query string parameters
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    cleaned_params: list[tuple[str, str]] = []

    for key, value in query_params:
        key_lower = key.lower()

        # Map sslmode parameter to asyncpg's ssl parameter
        if key_lower == "sslmode":
            val_lower = value.lower()
            if val_lower in ("disable", "false", "0"):
                cleaned_params.append(("ssl", "false"))
            elif val_lower in ("verify-full", "verify-ca"):
                cleaned_params.append(("ssl", "require"))
            else:
                cleaned_params.append(("ssl", value))
        # Strip libpq parameters that asyncpg doesn't support
        elif key_lower in UNSUPPORTED_LIBPQ_PARAMS:
            continue
        else:
            cleaned_params.append((key, value))

    # 3. Reconstruct URL with cleaned query string
    new_query = urlencode(cleaned_params)
    return urlunparse((
        scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))


# ---------------------------------------------------------------------------
# Lazy singletons — created on first access, not at import time
# ---------------------------------------------------------------------------
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        from app.core.config import settings  # local import avoids circular init

        _engine = create_async_engine(
            normalise_url(settings.database_url),
            echo=settings.environment == "development",
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory
