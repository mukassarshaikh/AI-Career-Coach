# Import all models here so Alembic's env.py can discover them via Base.metadata
from app.models.user import User
from app.models.resume import Resume, JobDescription, ResumeReport
from app.models.skill import SkillVector, MarketSkillReference, SkillGapReport
from app.models.learning import Roadmap, RoadmapItem
from app.models.career import ChatSession, ChatMessage
from app.models.logs import AiGenerationLog

__all__ = [
    "User",
    "Resume",
    "JobDescription",
    "ResumeReport",
    "SkillVector",
    "MarketSkillReference",
    "SkillGapReport",
    "Roadmap",
    "RoadmapItem",
    "ChatSession",
    "ChatMessage",
    "AiGenerationLog",
]
