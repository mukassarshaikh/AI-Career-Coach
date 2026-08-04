"""
learning_service.py — Business logic for Learning Intelligence (roadmap generation, item completion, & retrieval).

Responsibilities:
  - Generate sequenced roadmap items from a skill gap report via LLM.
  - Archive any existing active roadmap for the user (only 1 active roadmap per user at a time).
  - Create and save new Roadmap + RoadmapItem rows in Postgres.
  - Fetch full roadmaps with ordered items (by ID or active user status).
  - Update roadmap item status with strict user ownership validation and completed_at timestamps.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.learning import Roadmap, RoadmapItem
from app.models.skill import SkillGapReport
from app.services import llm_service

logger = logging.getLogger(__name__)


async def generate_roadmap_items(
    missing_skills: List[Dict[str, Any]],
    target_role: str,
    user_id: Optional[UUID] = None,
    db: Optional[AsyncSession] = None,
) -> List[Dict[str, Any]]:
    """
    Calls LLM service to convert a list of missing skills into sequenced roadmap item dictionaries.
    """
    return await llm_service.generate_roadmap_llm(
        missing_skills=missing_skills,
        target_role=target_role,
        user_id=user_id,
        db=db,
    )


async def create_roadmap(
    db: AsyncSession,
    user_id: UUID,
    skill_gap_report_id: UUID,
) -> Roadmap:
    """
    Creates a new active roadmap from a verified SkillGapReport.

    Process:
      1. Loads SkillGapReport by ID; verifies it exists and missing_skills is non-empty.
      2. Archives any existing 'active' roadmap for this user (only 1 active roadmap per user).
      3. Generates roadmap items via LLM.
      4. Inserts new Roadmap record and associated RoadmapItem records into database.

    Returns:
        The newly created Roadmap ORM instance with loaded items.
    """
    # 1. Fetch SkillGapReport
    stmt = select(SkillGapReport).where(SkillGapReport.id == skill_gap_report_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        raise ValueError(f"Skill gap report {skill_gap_report_id} not found.")

    missing_skills = report.missing_skills or []
    if not missing_skills:
        raise ValueError(
            f"Cannot generate roadmap for skill gap report {skill_gap_report_id}: missing_skills list is empty."
        )

    # 2. Archive any existing 'active' roadmap for this user
    archive_stmt = (
        update(Roadmap)
        .where(Roadmap.user_id == user_id, Roadmap.status == "active")
        .values(status="archived")
    )
    await db.execute(archive_stmt)

    # 3. Generate roadmap items via LLM
    item_dicts = await generate_roadmap_items(
        missing_skills=missing_skills,
        target_role=report.target_role,
        user_id=user_id,
        db=db,
    )

    # 4. Create new Roadmap row
    new_roadmap = Roadmap(
        id=uuid.uuid4(),
        user_id=user_id,
        skill_gap_report_id=skill_gap_report_id,
        status="active",
    )
    db.add(new_roadmap)

    # 5. Create RoadmapItem rows
    new_items = []
    for idx, item in enumerate(item_dicts, start=1):
        seq = item.get("sequence_order", idx)
        item_obj = RoadmapItem(
            id=uuid.uuid4(),
            roadmap_id=new_roadmap.id,
            skill_name=item.get("skill_name", "General Skill"),
            type=item.get("type", "course"),
            title=item.get("title", f"Learn {item.get('skill_name', 'Skill')}"),
            description=item.get("description"),
            url=item.get("url"),
            sequence_order=seq,
            difficulty=item.get("difficulty", "intermediate"),
            status="not_started",
        )
        new_items.append(item_obj)

    if new_items:
        db.add_all(new_items)

    await db.commit()

    # Re-fetch roadmap with items eagerly loaded and sorted by sequence_order
    full_roadmap = await get_roadmap_by_id(db=db, roadmap_id=new_roadmap.id, user_id=user_id)
    return full_roadmap or new_roadmap


async def get_roadmap_by_id(
    db: AsyncSession,
    roadmap_id: UUID,
    user_id: Optional[UUID] = None,
) -> Optional[Roadmap]:
    """
    Fetches a Roadmap by ID with all associated items eager-loaded and ordered by sequence_order.
    Optionally enforces user ownership if user_id is provided.
    """
    stmt = (
        select(Roadmap)
        .where(Roadmap.id == roadmap_id)
        .options(selectinload(Roadmap.items))
    )
    if user_id:
        stmt = stmt.where(Roadmap.user_id == user_id)

    result = await db.execute(stmt)
    roadmap = result.scalar_one_or_none()

    if roadmap and roadmap.items:
        roadmap.items.sort(key=lambda x: x.sequence_order)

    return roadmap


async def get_active_roadmap_by_user_id(
    db: AsyncSession,
    user_id: UUID,
) -> Optional[Roadmap]:
    """
    Fetches the current active Roadmap for the specified user with all items eager-loaded.
    """
    stmt = (
        select(Roadmap)
        .where(Roadmap.user_id == user_id, Roadmap.status == "active")
        .options(selectinload(Roadmap.items))
        .order_by(Roadmap.created_at.desc())
    )
    result = await db.execute(stmt)
    roadmap = result.scalar_one_or_none()

    if roadmap and roadmap.items:
        roadmap.items.sort(key=lambda x: x.sequence_order)

    return roadmap


async def update_roadmap_item_status(
    db: AsyncSession,
    item_id: UUID,
    user_id: UUID,
    new_status: str,
) -> Optional[Tuple[RoadmapItem, Optional[str]]]:
    """
    Updates the status of a RoadmapItem after performing a mandatory ownership check
    (joins through Roadmap to verify Roadmap.user_id == user_id).

    If new_status is 'completed', sets completed_at to current UTC time. Otherwise sets completed_at to None.
    If new_status is 'completed', also retrieves the target_role from the underlying SkillGapReport
    to allow background recalculation.

    Returns:
        Tuple of (updated RoadmapItem, target_role) or None if item not found / unauthorized.
    """
    # Query item joined with its parent Roadmap
    stmt = (
        select(RoadmapItem, Roadmap)
        .join(Roadmap, RoadmapItem.roadmap_id == Roadmap.id)
        .where(RoadmapItem.id == item_id, Roadmap.user_id == user_id)
    )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        logger.warning(f"RoadmapItem {item_id} not found for user_id={user_id} (ownership check failed).")
        return None

    item, roadmap = row

    item.status = new_status
    if new_status == "completed":
        item.completed_at = datetime.now(timezone.utc)
    else:
        item.completed_at = None

    target_role = None
    if new_status == "completed" and roadmap.skill_gap_report_id:
        # Fetch target_role from SkillGapReport
        gap_stmt = select(SkillGapReport.target_role).where(SkillGapReport.id == roadmap.skill_gap_report_id)
        gap_res = await db.execute(gap_stmt)
        target_role = gap_res.scalar_one_or_none()

    await db.commit()
    await db.refresh(item)

    return item, target_role
