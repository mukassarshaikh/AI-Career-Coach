"""
Arq WorkerSettings — entrypoint for the Arq job worker process.

Run with:
    arq app.workers.worker_settings.WorkerSettings
    OR:
    python -m app.workers.worker_settings
"""

import logging

from arq.connections import RedisSettings
from arq.worker import run_worker

from app.core.config import settings
from app.services import embedding_service
from app.workers.jobs.analyze_keywords import analyze_keywords
from app.workers.jobs.compute_skill_gap import compute_skill_gap
from app.workers.jobs.generate_roadmap import generate_roadmap
from app.workers.jobs.generate_skill_vector import generate_skill_vector
from app.workers.jobs.parse_resume import parse_resume
from app.workers.jobs.recalculate_skill_vector import recalculate_skill_vector
from app.workers.jobs.score_resume import score_resume

logger = logging.getLogger(__name__)


async def startup(ctx: dict):
    """Worker startup: create a shared DB session factory for jobs and warm up embedding model."""
    from app.core.db import get_session_factory

    ctx["db_factory"] = get_session_factory()

    logger.info("Warming up embedding model at worker startup...")
    embedding_service.generate_embedding("warmup")
    logger.info("Embedding model warmed up and ready")


async def shutdown(ctx: dict):
    """Worker shutdown: dispose of the engine if initialized."""
    from app.core.db import _engine

    if _engine is not None:
        await _engine.dispose()


class WorkerSettings:
    """
    Arq WorkerSettings.
    Registers all Phase 1 and Phase 2 job functions (`parse_resume`, `score_resume`, `analyze_keywords`, `generate_skill_vector`, `compute_skill_gap`, `generate_roadmap`, `recalculate_skill_vector`).
    """

    functions = [
        parse_resume,
        score_resume,
        analyze_keywords,
        generate_skill_vector,
        compute_skill_gap,
        generate_roadmap,
        recalculate_skill_vector,
    ]

    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 300  # 5-minute max per job


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_worker(WorkerSettings)

