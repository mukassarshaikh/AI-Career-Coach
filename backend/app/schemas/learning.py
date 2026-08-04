"""
Learning Intelligence Pydantic schemas for request/response serialization.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GenerateRoadmapRequest(BaseModel):
    """Request payload to generate a learning roadmap from a skill gap report."""

    skill_gap_report_id: UUID = Field(..., description="ID of the SkillGapReport to generate a roadmap for")


class GenerateRoadmapResponse(BaseModel):
    """Response returned when a roadmap generation job is enqueued."""

    skill_gap_report_id: UUID
    job_id: str = Field(..., description="ID of the background Arq job")
    message: str = Field(..., description="Status message")


class RoadmapItemResponse(BaseModel):
    """Response model for an individual roadmap item."""

    id: UUID
    roadmap_id: UUID
    skill_name: str
    type: str = Field(..., description="Item type: course, article, project, milestone")
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    sequence_order: int
    difficulty: str = Field(..., description="Difficulty: beginner, intermediate, advanced")
    status: str = Field("not_started", description="Status: not_started, in_progress, completed")
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RoadmapResponse(BaseModel):
    """Response model for a full roadmap with ordered items."""

    id: UUID
    user_id: UUID
    skill_gap_report_id: UUID
    status: str = Field("active", description="Status: active, completed, archived")
    created_at: datetime
    updated_at: datetime
    items: List[RoadmapItemResponse] = Field(default_factory=list, description="Sequenced list of roadmap items")

    model_config = ConfigDict(from_attributes=True)
