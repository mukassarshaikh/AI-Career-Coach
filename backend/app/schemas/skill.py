"""
Skill Intelligence Pydantic schemas for request/response serialization.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GenerateSkillVectorRequest(BaseModel):
    """Request payload for triggering skill vector generation from a resume."""

    resume_id: UUID = Field(..., description="ID of the parsed resume to extract skills from")


class GenerateSkillVectorResponse(BaseModel):
    """Response returned after enqueueing skill vector generation."""

    resume_id: UUID
    job_id: str
    message: str = Field("Skill vector generation job enqueued.", description="Status message")

    model_config = ConfigDict(from_attributes=True)


class ComputeSkillGapRequest(BaseModel):
    """Request payload for triggering skill gap report computation."""

    target_role: str = Field(
        ...,
        min_length=2,
        description="Target role title (e.g. 'Backend Engineer', 'Data Analyst')",
    )


class ComputeSkillGapResponse(BaseModel):
    """Response returned after enqueueing skill gap computation."""

    target_role: str
    job_id: str
    message: str = Field("Skill gap report computation enqueued.", description="Status message")

    model_config = ConfigDict(from_attributes=True)


class SkillGapReportResponse(BaseModel):
    """Schema for returning skill gap evaluation report details."""

    id: UUID
    user_id: UUID
    skill_vector_id: UUID
    target_role: str
    missing_skills: List[Dict[str, Any]] = Field(
        ...,
        description="Array of missing skills ranked by demand_weight (skill, demand_weight, importance, status)",
    )
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
