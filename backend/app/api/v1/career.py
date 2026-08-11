"""
Career Intelligence API routes — /api/v1/career/*

Endpoints:
  - POST /api/v1/career/chat/session: Create a new chat session (general / mock_interview / career_strategy).
  - POST /api/v1/career/chat/{session_id}/message: Send user message, stream LLM response via SSE (rate-limited 20/hr).
  - GET /api/v1/career/chat/{session_id}/history: Get complete message history for a session.
"""

import logging
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.career import (
    ChatHistoryResponse,
    ChatMessageResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    SendMessageRequest,
)
from app.services import career_service, llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/career", tags=["career"])


@router.post(
    "/chat/session",
    response_model=CreateSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a chat session",
    description="Creates a new chat session with a specified context type (general, mock_interview, or career_strategy).",
)
async def create_chat_session_endpoint(
    body: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CreateSessionResponse:
    """
    Creates a new chat session for the authenticated user.
    """
    session = await career_service.create_session(
        db=db,
        user_id=current_user.id,
        context_type=body.context_type.value,
    )
    return CreateSessionResponse.model_validate(session)


@router.get(
    "/chat/{session_id}/history",
    response_model=ChatHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chat session history",
    description="Fetches full message history for a specific chat session ordered by creation time ascending.",
)
async def get_chat_history_endpoint(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatHistoryResponse:
    """
    Retrieves full conversation history for an owned chat session.
    """
    session = await career_service.get_session(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    history = await career_service.get_session_history(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
    )

    msg_responses = [ChatMessageResponse.model_validate(msg) for msg in history]
    return ChatHistoryResponse(
        session_id=session_id,
        messages=msg_responses,
    )


@router.post(
    "/chat/{session_id}/message",
    summary="Send message and stream response",
    description="Sends a user message, streams the assistant's response via SSE tokens, and persists history upon completion.",
)
@limiter.limit("20/hour")
async def send_chat_message_endpoint(
    session_id: UUID,
    request: Request,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Core conversational endpoint:
    1. Validates session ownership.
    2. Saves user's message to DB.
    3. Assembles full conversation history and system prompt with dynamic candidate profile data.
    4. Streams Groq response via SSE (media_type="text/event-stream").
    5. Saves full assistant response to DB upon stream completion.
    Rate limited to 20 requests per hour per user.
    """
    session = await career_service.get_session(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    # Save the incoming user message
    await career_service.save_message(
        db=db,
        session_id=session_id,
        role="user",
        content=body.content,
    )

    # Fetch conversation history (includes the user message just saved)
    history = await career_service.get_session_history(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
    )
    messages = [{"role": msg.role, "content": msg.content} for msg in history]

    # Build dynamic candidate profile system prompt
    system_prompt = await career_service.build_system_prompt(
        db=db,
        user_id=current_user.id,
        context_type=session.context_type,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        collected_chunks = []
        try:
            async for text_chunk in llm_service.stream_chat_response(
                messages=messages,
                system_prompt=system_prompt,
                user_id=current_user.id,
                db=db,
            ):
                collected_chunks.append(text_chunk)
                formatted = text_chunk.replace("\n", "\ndata: ")
                yield f"data: {formatted}\n\n"
        except Exception as exc:
            logger.error(f"Error during SSE chat message streaming: {exc}")
            formatted_err = f"data: [ERROR: {str(exc)}]\n\n"
            yield formatted_err

        # Save assistant message to DB after stream completes
        full_assistant_message = "".join(collected_chunks)
        if full_assistant_message:
            try:
                await career_service.save_message(
                    db=db,
                    session_id=session_id,
                    role="assistant",
                    content=full_assistant_message,
                )
            except Exception as exc:
                logger.error(f"Failed to save assistant chat message after streaming: {exc}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
