"""
Dashboard Pydantic schemas for consolidated metrics.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DashboardSummaryResponse(BaseModel):
    """Consolidated summary response for platform dashboard."""

    resume_score: Optional[int] = Field(None, description="Latest ATS resume score (0-100)")
    missing_skills_count: int = Field(0, description="Total missing skills in latest gap report")
    target_role: Optional[str] = Field(None, description="Target career role")
    roadmap_total_items: int = Field(0, description="Total items in active roadmap")
    roadmap_completed_items: int = Field(0, description="Completed items in active roadmap")
    roadmap_completion_percentage: float = Field(0.0, description="Roadmap completion percentage (0-100)")
    active_roadmap_id: Optional[UUID] = Field(None, description="ID of current active roadmap")

    model_config = ConfigDict(from_attributes=True)
