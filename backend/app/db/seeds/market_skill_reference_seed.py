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
    
    # 1. Bulk query all existing market skill reference records in 1 network call
    existing_stmt = select(MarketSkillReference)
    existing_records = (await db.execute(existing_stmt)).scalars().all()
    existing_map = {(r.role_title, r.skill_name): r for r in existing_records}

    # 2. Batch generate 384-dim embeddings for all skills in 1 fast async thread pass
    skill_names = [item["skill_name"] for item in STARTER_MARKET_SKILLS]
    vectors_384 = await embedding_service.generate_embeddings_batch_async(skill_names)

    processed_count = 0
    new_objects = []

    for idx, item in enumerate(STARTER_MARKET_SKILLS):
        role_title = item["role_title"]
        skill_name = item["skill_name"]
        demand_weight = item["demand_weight"]
        vector_384 = vectors_384[idx] if idx < len(vectors_384) else embedding_service.generate_embedding(skill_name)

        existing = existing_map.get((role_title, skill_name))
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
            new_objects.append(new_ref)

        processed_count += 1

    if new_objects:
        db.add_all(new_objects)

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
