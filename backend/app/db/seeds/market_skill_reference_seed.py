"""
market_skill_reference_seed.py — Seed script to populate `market_skill_reference` table.

Reads starter dataset from `market_skill_reference_data.py`, generates a 384-dim vector
embedding per skill_name via `embedding_service`, and performs an idempotent upsert.

To run manually:
    cd backend
    python -m app.db.seeds.market_skill_reference_seed
"""

import asyncio
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session_factory
from app.db.seeds.market_skill_reference_data import STARTER_MARKET_SKILLS, STARTER_SOURCE
from app.models.skill import MarketSkillReference
from app.services import embedding_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_market_skill_reference(db: AsyncSession) -> int:
    """
    Idempotently seeds the `market_skill_reference` table with starter skills & embeddings.

    Args:
        db: SQLAlchemy async database session.

    Returns:
        The total count of records inserted or updated.
    """
    logger.info(f"Beginning market skill reference seeding ({len(STARTER_MARKET_SKILLS)} items)...")
    processed_count = 0

    for item in STARTER_MARKET_SKILLS:
        role_title = item["role_title"]
        skill_name = item["skill_name"]
        demand_weight = item["demand_weight"]

        # Generate 384-dim embedding vector via local embedding_service
        vector_384 = embedding_service.generate_embedding(skill_name)

        # Idempotent upsert check on natural key (role_title, skill_name)
        stmt = select(MarketSkillReference).where(
            MarketSkillReference.role_title == role_title,
            MarketSkillReference.skill_name == skill_name,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.demand_weight = demand_weight
            existing.vector = vector_384
            existing.source = STARTER_SOURCE
        else:
            new_ref = MarketSkillReference(
                role_title=role_title,
                skill_name=skill_name,
                demand_weight=demand_weight,
                vector=vector_384,
                source=STARTER_SOURCE,
            )
            db.add(new_ref)

        processed_count += 1

    await db.commit()
    logger.info(f"Successfully seeded/updated {processed_count} market_skill_reference records.")
    return processed_count


async def run_seed() -> None:
    """Standalone CLI entrypoint for running the seed script."""
    session_factory = get_session_factory()
    async with session_factory() as db:
        await seed_market_skill_reference(db)


if __name__ == "__main__":
    asyncio.run(run_seed())
