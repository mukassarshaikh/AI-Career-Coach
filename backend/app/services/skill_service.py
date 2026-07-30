"""
skill_service.py — Skill extraction, vector embedding, and skill-gap computation (Phase 1).

Handles:
  - Extracting skills list from a parsed resume (`parsed_json`)
  - Generating 384-dim skill vector embeddings via `embedding_service`
  - Upserting a single `SkillVector` row per user in Postgres
  - Computing skill gap reports against market skill references ranked by demand_weight
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.models.skill import MarketSkillReference, SkillGapReport, SkillVector
from app.services import embedding_service

logger = logging.getLogger(__name__)


def extract_skills_from_parsed_json(parsed_json: Optional[Dict[str, Any]]) -> List[str]:
    """
    Extracts a flat list of unique skill strings from a resume's `parsed_json` object.

    Handles both dictionary structures (`technical`, `tools`, `soft_skills`)
    and fallback list of strings.
    """
    if not parsed_json or "skills" not in parsed_json:
        return []

    skills_obj = parsed_json["skills"]
    extracted: set[str] = set()

    if isinstance(skills_obj, dict):
        for category, items in skills_obj.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str) and item.strip():
                        extracted.add(item.strip())
            elif isinstance(items, str) and items.strip():
                extracted.add(items.strip())
    elif isinstance(skills_obj, list):
        for item in skills_obj:
            if isinstance(item, str) and item.strip():
                extracted.add(item.strip())

    return sorted(list(extracted))


async def get_skill_vector_by_user_id(
    db: AsyncSession,
    user_id: UUID,
) -> Optional[SkillVector]:
    """
    Fetches the single `SkillVector` record for the given user_id if it exists.
    """
    stmt = select(SkillVector).where(SkillVector.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def upsert_user_skill_vector(
    db: AsyncSession,
    resume: Resume,
) -> SkillVector:
    """
    Extracts skills from `resume.parsed_json`, generates a 384-dim embedding vector,
    and upserts the single `SkillVector` row for the user (updating existing if present).

    Args:
        db: SQLAlchemy async database session.
        resume: Parsed Resume ORM model instance.

    Returns:
        The updated or newly created `SkillVector` ORM model instance.
    """
    if not resume.parsed_json:
        raise ValueError(
            f"Cannot generate skill vector for resume {resume.id}: parsed_json is null. Resume must be parsed first."
        )

    # 1. Extract skills list
    raw_skills_list = extract_skills_from_parsed_json(resume.parsed_json)
    skills_text_blob = f"Candidate competencies and skills: {', '.join(raw_skills_list)}"

    # 2. Generate 384-dimensional vector embedding
    vector_384 = embedding_service.generate_embedding(skills_text_blob)

    raw_skills_dict = {
        "skills": raw_skills_list,
        "count": len(raw_skills_list),
    }

    # 3. Check for existing SkillVector record for this user (upsert model)
    existing_vector = await get_skill_vector_by_user_id(db, user_id=resume.user_id)

    if existing_vector:
        logger.info(f"Updating existing SkillVector for user_id={resume.user_id}")
        existing_vector.resume_id = resume.id
        existing_vector.vector = vector_384
        existing_vector.raw_skills = raw_skills_dict
        target_vector = existing_vector
    else:
        logger.info(f"Creating new SkillVector for user_id={resume.user_id}")
        target_vector = SkillVector(
            user_id=resume.user_id,
            resume_id=resume.id,
            vector=vector_384,
            raw_skills=raw_skills_dict,
        )
        db.add(target_vector)

    await db.commit()
    await db.refresh(target_vector)

    return target_vector


async def get_latest_skill_gap_report(
    db: AsyncSession,
    user_id: UUID,
) -> Optional[SkillGapReport]:
    """
    Fetches the most recent SkillGapReport for the given user_id.
    """
    stmt = (
        select(SkillGapReport)
        .where(SkillGapReport.user_id == user_id)
        .order_by(SkillGapReport.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def compute_user_skill_gap(
    db: AsyncSession,
    user_id: UUID,
    target_role: str,
) -> SkillGapReport:
    """
    Computes a skill gap report for a candidate against a target role:
      1. Fetches candidate's SkillVector. Fails cleanly if none exists.
      2. Queries MarketSkillReference matching target_role.
      3. Identifies skills in MarketSkillReference absent or weak in candidate's skills.
      4. Ranks missing skills by demand_weight (descending).
      5. Creates and returns a new SkillGapReport DB record.
    """
    # 1. Fetch candidate's SkillVector
    skill_vector = await get_skill_vector_by_user_id(db, user_id=user_id)
    if not skill_vector:
        raise ValueError(
            f"Cannot compute skill gap for user {user_id}: no skill vector found. Run generate_skill_vector job first."
        )

    # Candidate skills normalized set
    raw_skills = skill_vector.raw_skills.get("skills", []) if skill_vector.raw_skills else []
    candidate_skills_set = {str(s).lower().strip() for s in raw_skills}

    # 2. Query market skill references for target_role
    stmt = (
        select(MarketSkillReference)
        .where(func.lower(MarketSkillReference.role_title) == target_role.lower())
        .order_by(MarketSkillReference.demand_weight.desc())
    )
    result = await db.execute(stmt)
    market_refs = result.scalars().all()

    # Fallback partial matching if exact role match returns empty
    if not market_refs:
        stmt = (
            select(MarketSkillReference)
            .where(MarketSkillReference.role_title.ilike(f"%{target_role}%"))
            .order_by(MarketSkillReference.demand_weight.desc())
        )
        result = await db.execute(stmt)
        market_refs = result.scalars().all()

    # If still empty (e.g. unseeded custom role), fallback to top global market references
    if not market_refs:
        stmt = (
            select(MarketSkillReference)
            .order_by(MarketSkillReference.demand_weight.desc())
            .limit(20)
        )
        result = await db.execute(stmt)
        market_refs = result.scalars().all()

    # 3. Identify missing skills and rank by demand_weight
    missing_skills_list: list[dict[str, Any]] = []

    for ref in market_refs:
        ref_skill_clean = ref.skill_name.lower().strip()
        # Check exact or substring overlap
        is_matched = any(
            ref_skill_clean in cand_skill or cand_skill in ref_skill_clean
            for cand_skill in candidate_skills_set
        )

        if not is_matched:
            importance_level = (
                "high" if ref.demand_weight >= 0.85
                else ("medium" if ref.demand_weight >= 0.75 else "low")
            )
            missing_skills_list.append({
                "skill": ref.skill_name,
                "demand_weight": round(ref.demand_weight, 2),
                "importance": importance_level,
                "status": "missing",
            })

    # Sort descending by demand_weight (FR-2.4 requirement)
    missing_skills_list.sort(key=lambda x: x["demand_weight"], reverse=True)

    # 4. Insert SkillGapReport database record
    report = SkillGapReport(
        user_id=user_id,
        skill_vector_id=skill_vector.id,
        target_role=target_role,
        missing_skills=missing_skills_list,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return report
