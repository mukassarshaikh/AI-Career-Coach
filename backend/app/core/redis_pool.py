"""
Shared Arq/Redis connection pool.

A single pool is created once at application startup and reused for every
enqueue/status-check call, instead of opening and closing a new connection
per request. This avoids repeatedly paying Redis's connect/auth handshake
(and its retry/backoff delay) on every poll tick, and makes a genuine
Redis outage fail fast and visibly instead of masking it behind a fresh
per-call retry sequence.
"""

import logging

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from app.core.config import settings

logger = logging.getLogger(__name__)

_pool: ArqRedis | None = None


async def init_redis_pool() -> None:
    """Call once on FastAPI startup. Does not raise if Redis is unreachable —
    logs a clear warning instead, so the app can still start (e.g. to serve
    non-job endpoints), but every enqueue/status call will fail loudly and
    honestly until this is fixed, rather than silently pretending to work."""
    global _pool
    try:
        _pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        await _pool.ping()
        logger.info("Redis/Arq pool connected successfully.")
    except Exception as exc:
        _pool = None
        logger.warning(
            f"Redis unreachable at startup ({exc}). Background job endpoints "
            f"(upload parsing, scoring, keyword analysis) will return a 503 "
            f"error until this is resolved — they will NOT silently fake success."
        )


async def close_redis_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_redis_pool() -> ArqRedis:
    """Raises a clear RuntimeError if the pool isn't available — callers
    must turn this into a proper HTTP error, never a fabricated success."""
    if _pool is None:
        raise RuntimeError(
            "Redis/Arq pool is not available. Check REDIS_URL and that the "
            "Upstash/Redis instance is reachable."
        )
    return _pool
