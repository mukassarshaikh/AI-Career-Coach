"""
Arq WorkerSettings — entrypoint for the Arq job worker process.

Run with:
    arq app.workers.worker_settings.WorkerSettings

The worker runs as a separate process alongside uvicorn, sharing the same
codebase but consuming jobs from the Redis queue instead of handling HTTP.
"""

from arq.connections import RedisSettings

from app.core.config import settings
from app.workers.jobs.analyze_keywords import analyze_keywords
from app.workers.jobs.compute_skill_gap import compute_skill_gap
from app.workers.jobs.generate_skill_vector import generate_skill_vector
from app.workers.jobs.parse_resume import parse_resume
from app.workers.jobs.score_resume import score_resume


async def startup(ctx: dict):
    """Worker startup: create a shared DB session factory for jobs."""
    from app.core.db import get_session_factory
    ctx["db_factory"] = get_session_factory()


async def shutdown(ctx: dict):
    """Worker shutdown: dispose of the engine if initialized."""
    from app.core.db import _engine
    if _engine is not None:
        await _engine.dispose()


class WorkerSettings:
    """
    Arq WorkerSettings.
    Registers all Phase 1 job functions (`parse_resume`, `score_resume`, `analyze_keywords`, `generate_skill_vector`, `compute_skill_gap`).
    """
    functions = [
        parse_resume,
        score_resume,
        analyze_keywords,
        generate_skill_vector,
        compute_skill_gap,
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 300  # 5-minute max per job
