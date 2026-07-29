"""
Arq WorkerSettings — entrypoint for the Arq job worker process.

Run with:
    arq app.workers.worker_settings.WorkerSettings

The worker runs as a separate process alongside uvicorn, sharing the same
codebase but consuming jobs from the Redis queue instead of handling HTTP.

Job functions are registered in the `functions` list below. Each job file
should be a thin wrapper that calls into /services for the actual logic.
"""

from arq.connections import RedisSettings

from app.core.config import settings

# ---------------------------------------------------------------------------
# Job imports (uncomment as each job is implemented in Phase 1+)
# ---------------------------------------------------------------------------
# from app.workers.jobs.parse_resume import parse_resume
# from app.workers.jobs.score_resume import score_resume
# from app.workers.jobs.analyze_keywords import analyze_keywords
# from app.workers.jobs.generate_skill_vector import generate_skill_vector
# from app.workers.jobs.compute_skill_gap import compute_skill_gap
# from app.workers.jobs.generate_roadmap import generate_roadmap
# from app.workers.jobs.recalculate_skill_vector import recalculate_skill_vector


async def startup(ctx: dict):
    """Worker startup: create a shared DB session factory for jobs."""
    from app.core.db import AsyncSessionLocal
    ctx["db_factory"] = AsyncSessionLocal


async def shutdown(ctx: dict):
    """Worker shutdown: dispose of the engine."""
    from app.core.db import engine
    await engine.dispose()


class WorkerSettings:
    """
    Arq WorkerSettings.
    Add job functions to `functions` as they are implemented.
    """
    functions = []  # Phase 1: [parse_resume, score_resume, analyze_keywords, ...]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 300  # 5-minute max per job
