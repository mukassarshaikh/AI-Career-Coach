import logging
import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.models.skill import MarketSkillReference, SkillGapReport, SkillVector
from app.services import embedding_service

logger = logging.getLogger(__name__)


STATIC_ROLE_ALIASES: dict[str, list[str]] = {
    "senior react developer": ["Senior React Developer", "Frontend Engineer"],
    "react developer": ["Senior React Developer", "Frontend Engineer"],
    "react engineer": ["Senior React Developer", "Frontend Engineer"],
    "frontend developer": ["Frontend Engineer", "Senior React Developer"],
    "senior frontend engineer": ["Frontend Engineer", "Senior React Developer"],
    "frontend web developer": ["Frontend Engineer", "Senior React Developer"],
    "backend developer": ["Backend Engineer"],
    "senior backend engineer": ["Backend Engineer"],
    "python backend engineer": ["Backend Engineer"],
    "fullstack developer": ["Full-Stack Engineer"],
    "full stack developer": ["Full-Stack Engineer"],
    "senior fullstack engineer": ["Full-Stack Engineer"],
    "devops": ["DevOps Engineer"],
    "cloud architect": ["Cloud Solutions Architect"],
    "ml engineer": ["Machine Learning Engineer"],
    "ai engineer": ["AI / LLM Engineer"],
    "llm engineer": ["AI / LLM Engineer"],
    "data engineer": ["Data Engineer"],
    "data analyst": ["Data Analyst"],
}

SKILL_ALIASES: dict[str, set[str]] = {
    "react": {"react", "react.js", "reactjs", "react js"},
    "next.js": {"next.js", "nextjs", "next js"},
    "node.js": {"node.js", "nodejs", "node js"},
    "vue.js": {"vue.js", "vuejs", "vue js"},
    "typescript": {"typescript", "ts"},
    "javascript": {"javascript", "js"},
    "html5 / css3": {"html", "css", "html5", "css3", "html/css", "html5 / css3", "html5/css3"},
    "postgresql": {"postgresql", "postgres", "postgres db"},
    "aws architecture": {"aws", "amazon web services", "aws architecture", "aws cloud"},
}


def normalize_skill_name(s: str) -> str:
    """Normalizes a skill string for case-insensitive, whitespace-trimmed comparison."""
    if not s:
        return ""
    s_clean = s.lower().strip()
    s_clean = re.sub(r'[^\w\s\./\+\-#]', '', s_clean)
    return s_clean


def is_candidate_skill_matched(market_skill: str, candidate_skills_set: set[str]) -> bool:
    """
    Determines if candidate skills set contains or matches the market skill,
    accounting for exact match, normalized aliases, and word boundaries.
    """
    norm_market = normalize_skill_name(market_skill)
    if not norm_market:
        return False

    # 1. Exact match against normalized candidate skills set
    if norm_market in candidate_skills_set:
        return True

    # 2. Alias match
    for canonical, aliases in SKILL_ALIASES.items():
        if norm_market == canonical or norm_market in aliases:
            if any(cand in aliases or cand == canonical for cand in candidate_skills_set):
                return True

    # 3. Token set match (avoid false positives like "c" vs "c++", "java" vs "javascript")
    market_words = set(norm_market.split())
    for cand in candidate_skills_set:
        cand_words = set(cand.split())
        if len(norm_market) > 3 and (norm_market == cand or (market_words and market_words == cand_words)):
            return True

    return False


async def resolve_market_role(db: AsyncSession, target_role: str) -> Optional[str]:
    """
    Resolves user's target_role string to a valid role_title in MarketSkillReference.
    Tries exact match, static alias map, substring containment, and token overlap.
    Returns None if no matching market benchmark role is available.
    """
    if not target_role or not target_role.strip():
        return None

    clean_role = target_role.strip().lower()

    # 1. Exact case-insensitive match
    stmt = (
        select(MarketSkillReference.role_title)
        .where(func.lower(MarketSkillReference.role_title) == clean_role)
        .limit(1)
    )
    result = await db.execute(stmt)
    exact = result.scalar_one_or_none()
    if exact:
        return exact

    # 2. Static alias lookup (tries candidate role titles in preference order)
    if clean_role in STATIC_ROLE_ALIASES:
        candidates = STATIC_ROLE_ALIASES[clean_role]
        for candidate_title in candidates:
            stmt = (
                select(MarketSkillReference.role_title)
                .where(func.lower(MarketSkillReference.role_title) == candidate_title.lower())
                .limit(1)
            )
            res = await db.execute(stmt)
            if res.scalar_one_or_none():
                return candidate_title

    # 3. Fetch all role titles for substring and token matching
    stmt = select(MarketSkillReference.role_title).distinct()
    res = await db.execute(stmt)
    all_roles = res.scalars().all()

    for role in all_roles:
        r_lower = role.lower()
        if clean_role in r_lower or r_lower in clean_role:
            return role

    # 4. Token overlap check
    target_tokens = set(re.findall(r'\w+', clean_role))
    best_role = None
    best_score = 0
    for role in all_roles:
        role_tokens = set(re.findall(r'\w+', role.lower()))
        common = target_tokens.intersection(role_tokens)
        meaningful = {t for t in common if t not in {"senior", "junior", "lead", "engineer", "developer", "architect"}}
        if len(meaningful) > best_score:
            best_score = len(meaningful)
            best_role = role

    return best_role


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
      2. Resolves target_role to a market benchmark role in MarketSkillReference.
      3. Identifies skills in MarketSkillReference absent from candidate's skills.
      4. Deduplicates and ranks missing skills by demand_weight (descending).
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
    candidate_skills_set = {normalize_skill_name(str(s)) for s in raw_skills if str(s).strip()}

    # 2. Resolve target role to market benchmark role
    resolved_role = await resolve_market_role(db, target_role)
    if not resolved_role:
        raise ValueError(
            f"No benchmark market reference data available for target role '{target_role}'. Please select from available benchmark roles."
        )

    # Query market skill references exclusively for the resolved_role
    stmt = (
        select(MarketSkillReference)
        .where(func.lower(MarketSkillReference.role_title) == resolved_role.lower())
        .order_by(MarketSkillReference.demand_weight.desc())
    )
    result = await db.execute(stmt)
    market_refs = result.scalars().all()

    if not market_refs:
        raise ValueError(
            f"No market skill reference records found for resolved role '{resolved_role}'."
        )

    # 3. Identify missing skills, deduplicate by normalized skill name, and rank by demand_weight
    missing_skills_list: list[dict[str, Any]] = []
    seen_skills: set[str] = set()

    for ref in market_refs:
        norm_ref_skill = normalize_skill_name(ref.skill_name)
        if not norm_ref_skill or norm_ref_skill in seen_skills:
            continue

        if not is_candidate_skill_matched(ref.skill_name, candidate_skills_set):
            seen_skills.add(norm_ref_skill)
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

    # 4. Insert SkillGapReport database record with the user's requested target_role
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

