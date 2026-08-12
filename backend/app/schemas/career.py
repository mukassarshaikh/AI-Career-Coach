"""
Career Intelligence Pydantic schemas for request/response serialization.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CareerContextTypeEnum(str, Enum):
    GENERAL = "general"
    MOCK_INTERVIEW = "mock_interview"
    CAREER_STRATEGY = "career_strategy"


class CreateSessionRequest(BaseModel):
    """Request payload to create a new chat session."""

    context_type: CareerContextTypeEnum = Field(
        ...,
        description="Type of chat context: general, mock_interview, or career_strategy",
    )


class CreateSessionResponse(BaseModel):
    """Response model for a created chat session."""

    id: UUID
    name: Optional[str] = None
    context_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RenameSessionRequest(BaseModel):
    """Request payload to rename an existing chat session."""

    name: str = Field(..., min_length=1, max_length=200, description="New name for the session")


class DeleteSessionResponse(BaseModel):
    """Response payload for session deletion confirmation."""

    deleted: bool
    session_id: UUID


class SendMessageRequest(BaseModel):
    """Request payload to send a message in a chat session."""

    content: str = Field(..., min_length=1, description="Message text content")


class ChatMessageResponse(BaseModel):
    """Response model for a single chat message."""

    id: UUID
    session_id: UUID
    role: str = Field(..., description="Role: user or assistant")
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    """Response model for fetching complete chat history of a session."""

    session_id: UUID
    messages: List[ChatMessageResponse] = Field(
        default_factory=list, description="Ordered list of chat messages"
    )

    model_config = ConfigDict(from_attributes=True)


class ChatSessionPreviewResponse(BaseModel):
    """Response model for listing user chat sessions with message preview."""

    id: UUID
    name: Optional[str] = None
    context_type: str
    created_at: datetime
    preview: str = Field("New session", description="Preview snippet of the first message")

    model_config = ConfigDict(from_attributes=True)


