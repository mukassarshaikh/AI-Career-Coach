from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.redis_pool import close_redis_pool, init_redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes Redis connection pool on startup and closes it on shutdown.
    """
    # Startup — warm up Redis pool so any immediate job enqueue succeeds
    await init_redis_pool()
    yield
    await close_redis_pool()
    # Shutdown — close DB engine if it was initialised
    from app.core.db import _engine

    if _engine is not None:
        await _engine.dispose()


app = FastAPI(
    title="AI Career Coach API",
    version="0.1.0",
    description="Backend for the AI Career Coach platform.",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Rate Limiter — slowapi
# ---------------------------------------------------------------------------
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# CORS — restricted to the frontend origin only
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API v1 Routers
# ---------------------------------------------------------------------------
app.include_router(api_v1_router, prefix="/api/v1")
