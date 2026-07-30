"""
AI Career Coach — FastAPI application entry point.

Registers all routers, configures CORS, and handles startup/shutdown events.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth as auth_router
from app.api.v1 import health as health_router
from app.api.v1 import resume as resume_router
from app.api.v1 import skill as skill_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
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
# Routers
# ---------------------------------------------------------------------------
app.include_router(health_router.router, prefix="/api/v1")
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(resume_router.router, prefix="/api/v1")
app.include_router(skill_router.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "AI Career Coach API", "docs": "/docs"}
