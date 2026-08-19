"""
prune_ai_generation_logs.py — Arq worker job definition (Phase 4 Story 4.3).

Consumes scheduled log retention job from Redis:
  1. Computes UTC cutoff timestamp: datetime.now(timezone.utc) - timedelta(days=30).
  2. Executes database-side bulk DELETE from `ai_generation_logs` WHERE created_at < cutoff.
  3. Applies to all logs (user-associated and system-level with user_id=None) older than 30 days.
  4. Logs structured application log containing deleted row count.
  5. Idempotent and safe to run on any schedule.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from app.models.logs import AiGenerationLog

logger = logging.getLogger(__name__)


async def prune_ai_generation_logs(ctx: dict) -> dict:
    """
    Arq worker job that prunes `ai_generation_logs` records older than 30 days.
    """
    logger.info("Starting prune_ai_generation_logs background job...")

    db_factory = ctx.get("db_factory")
    if not db_factory:
        raise RuntimeError("Arq context missing 'db_factory'")

    # Timezone-aware UTC cutoff: 30 days ago
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    logger.info(f"Pruning AI generation logs created before UTC cutoff: {cutoff.isoformat()}")

    async with db_factory() as db:
        try:
            stmt = delete(AiGenerationLog).where(AiGenerationLog.created_at < cutoff)
            result = await db.execute(stmt)
            await db.commit()

            deleted_count = result.rowcount if hasattr(result, "rowcount") and result.rowcount is not None else 0
            logger.info(
                f"Successfully pruned {deleted_count} AI generation log record(s) older than 30 days (cutoff: {cutoff.isoformat()})."
            )
            return {
                "status": "complete",
                "cutoff": cutoff.isoformat(),
                "deleted_count": deleted_count,
            }
        except Exception as exc:
            logger.error(f"Failed to prune AI generation logs: {exc}")
            await db.rollback()
            return {
                "status": "failed",
                "error": str(exc),
            }
