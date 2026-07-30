"""
Resume Pydantic schemas for request/response serialization.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResumeUploadResponse(BaseModel):
    """Response returned after successfully uploading a resume file."""

    resume_id: UUID = Field(..., description="Unique identifier of the created resume record")
    file_url: str = Field(..., description="Cloudinary storage URL for the uploaded file")
    created_at: datetime = Field(..., description="Timestamp when the resume was uploaded")
    job_id: Optional[str] = Field(None, description="Arq async job ID for background processing")
    message: str = Field("Resume uploaded successfully", description="Status message")

    model_config = ConfigDict(from_attributes=True)


class ResumeResponse(BaseModel):
    """Schema for returning full resume record details."""

    id: UUID
    user_id: UUID
    file_url: str
    raw_text: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None
    ats_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobStatusResponse(BaseModel):
    """Schema for returning background job status (polling)."""

    job_id: str
    status: str = Field(..., description="Job status: queued, in_progress, complete, or failed")
    result: Optional[Dict[str, Any]] = Field(None, description="Result data if job completed")

    model_config = ConfigDict(from_attributes=True)


class ScoreResumeResponse(BaseModel):
    """Response returned after enqueueing resume scoring."""

    resume_id: UUID
    job_id: str
    message: str = Field("Resume scoring job enqueued.", description="Status message")

    model_config = ConfigDict(from_attributes=True)


class ResumeReportResponse(BaseModel):
    """Schema for returning resume evaluation report details."""

    id: UUID
    resume_id: UUID
    job_description_id: Optional[UUID] = None
    ats_breakdown: Optional[Dict[str, Any]] = Field(
        None, description="ATS sub-scores (overall_score, formatting, structure, parseability, feedback)"
    )
    grammar_suggestions: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of grammar, tone, and clarity suggestions"
    )
    keyword_gaps: Optional[List[Dict[str, Any]]] = Field(
        None, description="Missing keywords compared to JD (null until JD submission)"
    )
    action_items: Optional[List[Dict[str, Any]]] = Field(
        None, description="Prioritized improvement items (null until JD submission)"
    )
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobDescriptionCreate(BaseModel):
    """Request payload for submitting a target job description."""

    raw_text: str = Field(
        ...,
        min_length=10,
        description="Raw text content of the target job description",
    )


class SubmitJobDescriptionResponse(BaseModel):
    """Response returned after submitting a job description and enqueueing analysis."""

    job_description_id: UUID = Field(..., description="Unique identifier of the created Job Description record")
    resume_id: UUID = Field(..., description="Associated resume ID")
    job_id: str = Field(..., description="Arq async job ID for background keyword analysis")
    message: str = Field("Job description submitted; keyword analysis enqueued.", description="Status message")

    model_config = ConfigDict(from_attributes=True)
