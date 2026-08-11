"""
Career Intelligence service containing database interactions and system prompt assembly.
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career import ChatMessage, ChatSession
from app.models.learning import Roadmap, RoadmapItem
from app.models.resume import Resume
from app.models.skill import SkillGapReport
from app.models.user import User

logger = logging.getLogger(__name__)


async def create_session(db: AsyncSession, user_id: UUID, context_type: str) -> ChatSession:
    """Creates and persists a new ChatSession row for the user."""
    session = ChatSession(
        user_id=user_id,
        context_type=context_type,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: UUID, user_id: UUID) -> Optional[ChatSession]:
    """Fetches a ChatSession by ID and verifies user ownership."""
    stmt = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_session_history(db: AsyncSession, session_id: UUID, user_id: UUID) -> List[ChatMessage]:
    """Fetches all ChatMessage rows for a session ordered by created_at asc."""
    session = await get_session(db, session_id=session_id, user_id=user_id)
    if not session:
        return []

    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def save_message(db: AsyncSession, session_id: UUID, role: str, content: str) -> ChatMessage:
    """Saves a ChatMessage row for the specified session."""
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def build_system_prompt(db: AsyncSession, user_id: UUID, context_type: str) -> str:
    """
    Assembles dynamic Groq system prompt incorporating candidate context from DB.
    Pulls real user data: name, latest parsed resume skills & experience, latest
    skill gap report target_role & missing_skills, and roadmap progress.
    """
    # 1. Fetch User details
    user_stmt = select(User).where(User.id == user_id)
    user_res = await db.execute(user_stmt)
    user = user_res.scalar_one_or_none()
    user_name = user.name if (user and user.name) else "Candidate"
    user_target_role = user.target_role if (user and user.target_role) else None

    # 2. Fetch Latest Resume
    resume_stmt = (
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
    )
    resume_res = await db.execute(resume_stmt)
    latest_resume = resume_res.scalars().first()

    resume_skills_str = "None listed"
    experience_str = "None listed"

    if latest_resume and latest_resume.parsed_json:
        pj = latest_resume.parsed_json
        # Extract technical skills
        skills_obj = pj.get("skills")
        raw_tech_skills = []
        if isinstance(skills_obj, dict):
            raw_tech_skills = skills_obj.get("technical", [])
        elif isinstance(skills_obj, list):
            raw_tech_skills = skills_obj

        if raw_tech_skills:
            resume_skills_str = ", ".join(raw_tech_skills[:15])

        # Extract most recent experience
        exp_list = pj.get("experience", [])
        if isinstance(exp_list, list) and len(exp_list) > 0:
            first_exp = exp_list[0]
            if isinstance(first_exp, dict):
                role = first_exp.get("role", "")
                company = first_exp.get("company", "")
                if role and company:
                    experience_str = f"{role} at {company}"
                elif role:
                    experience_str = role
                elif company:
                    experience_str = company

    # 3. Fetch Latest Skill Gap Report
    gap_stmt = (
        select(SkillGapReport)
        .where(SkillGapReport.user_id == user_id)
        .order_by(SkillGapReport.created_at.desc())
    )
    gap_res = await db.execute(gap_stmt)
    latest_gap = gap_res.scalars().first()

    target_role_str = "Not set"
    skill_gaps_str = "None identified"

    if latest_gap:
        if latest_gap.target_role:
            target_role_str = latest_gap.target_role
        elif user_target_role:
            target_role_str = user_target_role

        missing = latest_gap.missing_skills
        if isinstance(missing, list) and missing:
            top_gaps = []
            for item in missing[:5]:
                if isinstance(item, dict) and "skill" in item:
                    top_gaps.append(item["skill"])
                elif isinstance(item, str):
                    top_gaps.append(item)
            if top_gaps:
                skill_gaps_str = ", ".join(top_gaps)
    elif user_target_role:
        target_role_str = user_target_role

    # 4. Fetch Roadmap Progress
    roadmap_stmt = (
        select(Roadmap)
        .where(Roadmap.user_id == user_id, Roadmap.status == "active")
        .order_by(Roadmap.created_at.desc())
    )
    roadmap_res = await db.execute(roadmap_stmt)
    active_roadmap = roadmap_res.scalars().first()

    if not active_roadmap:
        fallback_stmt = (
            select(Roadmap)
            .where(Roadmap.user_id == user_id)
            .order_by(Roadmap.created_at.desc())
        )
        fallback_res = await db.execute(fallback_stmt)
        active_roadmap = fallback_res.scalars().first()

    completed_count = 0
    total_count = 0

    if active_roadmap:
        items_stmt = select(RoadmapItem).where(RoadmapItem.roadmap_id == active_roadmap.id)
        items_res = await db.execute(items_stmt)
        items = items_res.scalars().all()
        total_count = len(items)
        completed_count = sum(1 for item in items if item.status == "completed")

    # Assemble Part 1 (static) and Part 2 (dynamic candidate profile)
    part1 = (
        "You are an expert career advisor for AI Career Coach. You give direct, specific, evidence-based career guidance. "
        "You do not give generic advice — everything you say references the candidate's actual profile below. "
        "For legal, visa, or compensation questions, note you are not a licensed advisor and recommend consulting a professional. "
        "Keep responses concise and actionable."
    )

    part2 = (
        f"CANDIDATE PROFILE:\n"
        f"Name: {user_name}\n"
        f"Target Role: {target_role_str}\n"
        f"Resume Skills: {resume_skills_str}\n"
        f"Experience: {experience_str}\n"
        f"Skill Gaps: {skill_gaps_str}\n"
        f"Learning Progress: {completed_count}/{total_count} roadmap items completed\n"
        f"Context type: {context_type}"
    )

    prompt = f"{part1}\n\n{part2}"

    if context_type == "mock_interview":
        prompt += (
            "\n\nYou are conducting a mock interview for the target role. "
            "Ask one question at a time, wait for the candidate's answer, then give specific feedback before the next question. "
            "Start by introducing the interview format."
        )
    elif context_type == "career_strategy":
        prompt += (
            "\n\nFocus on actionable career strategy: promotion paths, skill investment priorities, "
            "and positioning advice based on their specific gap profile."
        )

    return prompt
