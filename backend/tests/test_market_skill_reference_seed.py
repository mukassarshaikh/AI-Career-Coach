"""
Pytest test suite for market_skill_reference seed script, starter dataset structure, 384-dim embeddings, and idempotency.

Run with:
    pytest tests/test_market_skill_reference_seed.py -v
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.db.seeds.market_skill_reference_data import STARTER_MARKET_SKILLS, STARTER_SOURCE
from app.db.seeds.market_skill_reference_seed import seed_market_skill_reference
from app.models.skill import MarketSkillReference


# ---------------------------------------------------------------------------
# 1. Dataset Verification
# ---------------------------------------------------------------------------
def test_starter_dataset_structure_and_coverage():
    """Verify starter dataset covers 30 roles with valid demand weights and skills."""
    unique_roles = {item["role_title"] for item in STARTER_MARKET_SKILLS}
    assert len(unique_roles) == 30, f"Expected 30 unique roles, got {len(unique_roles)}"

    for item in STARTER_MARKET_SKILLS:
        assert "role_title" in item
        assert "skill_name" in item
        assert "demand_weight" in item
        assert 0.0 <= item["demand_weight"] <= 1.0, f"Invalid demand_weight: {item['demand_weight']}"


# ---------------------------------------------------------------------------
# 2. Seed Execution & Idempotency Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_seed_market_skill_reference_execution_and_idempotency():
    """
    Verify seed_market_skill_reference generates 384-dim embeddings and is idempotent
    (re-running does not produce duplicate records).
    """
    seeded_records: dict[tuple[str, str], MarketSkillReference] = {}
    mock_db = AsyncMock()

    # Mock DB query behavior for idempotent upsert check
    async def mock_execute(stmt):
        # Extract role_title and skill_name from WHERE clause if possible
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        return mock_result

    from unittest.mock import MagicMock
    mock_db.execute = AsyncMock(side_effect=mock_execute)

    # Track objects added to db
    added_objects = []
    def mock_add(obj):
        if isinstance(obj, MarketSkillReference):
            added_objects.append(obj)
            seeded_records[(obj.role_title, obj.skill_name)] = obj

    mock_db.add = mock_add

    with patch("app.services.embedding_service.generate_embedding", return_value=[0.1] * 384):
        # First Run
        count1 = await seed_market_skill_reference(mock_db)
        assert count1 == len(STARTER_MARKET_SKILLS)
        assert len(added_objects) == len(STARTER_MARKET_SKILLS)

        # Verify attributes on inserted objects
        sample_ref = added_objects[0]
        assert isinstance(sample_ref, MarketSkillReference)
        assert len(sample_ref.vector) == 384
        assert 0.0 <= sample_ref.demand_weight <= 1.0
        assert sample_ref.source == STARTER_SOURCE

        # Second Run — Mock existing records found in DB to test idempotency
        added_objects.clear()
        async def mock_execute_run2(stmt):
            # Simulate returning existing object for update
            mock_res = MagicMock()
            mock_res.scalar_one_or_none.return_value = sample_ref
            return mock_res

        mock_db.execute = AsyncMock(side_effect=mock_execute_run2)

        count2 = await seed_market_skill_reference(mock_db)
        assert count2 == len(STARTER_MARKET_SKILLS)
        # Idempotency check: no new rows added on 2nd run because existing records were updated in place
        assert len(added_objects) == 0
