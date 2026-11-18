"""Chat API endpoints for ShopEasy customer support."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.runner import run_agent
from app.core.auth import get_current_user
from app.core.rate_limit import check_rate_limit
from app.db import SessionLocal, get_db
from app.models.message import Message
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])

MAX_MESSAGE_LENGTH = 1000


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=MAX_MESSAGE_LENGTH,
        description="Customer question capped at 1,000 characters",
    )
    session_id: Optional[str] = Field(
        None, description="Optional existing session ID to continue a conversation"
    )


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[str]
    approval_required: Optional[Dict[str, Any]] = None


class MessageItem(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def send_chat_message(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Process a customer question through the Agent pipeline and persist conversation history.

    - Enforces rate limiting (15 req/min)
    - Validates message input (max 1,000 chars)
    - Assigns or reuses a session_id
    - Saves user message to the messages table
    - Runs Agent loop with tools
    - Saves assistant response to the messages table
    """
    check_rate_limit(request, current_user=current_user)
    clean_message = payload.message.strip()
    if not clean_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty or only whitespace.",
        )

    # 1. Determine or generate session_id
    session_id = payload.session_id.strip() if payload.session_id else str(uuid.uuid4())

    # 2. Persist User Message
    user_record = Message(
        session_id=session_id,
        role="user",
        content=clean_message,
        sources=None,
    )
    db.add(user_record)
    db.commit()

    # 3. Run Agent Loop with Tools
    agent_result = run_agent(clean_message, user_id=current_user.id)

    # 4. Persist Assistant Response with Cited Sources
    assistant_record = Message(
        session_id=session_id,
        role="assistant",
        content=agent_result.answer,
        sources=agent_result.sources,
    )
    db.add(assistant_record)
    db.commit()

    return ChatResponse(
        session_id=session_id,
        answer=agent_result.answer,
        sources=agent_result.sources,
        approval_required=agent_result.approval_required,
    )


@router.post("/stream")
def stream_chat_message(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Stream answer tokens using Server-Sent Events (SSE) via the Agent Loop.

    1. Enforces rate limiting (15 req/min)
    2. Validates message input (max 1,000 chars)
    3. Assigns or reuses session_id
    4. Persists user message
    5. Executes Agent Runner (tool calling, policy search, order queries)
    6. Streams answer tokens as SSE data events
    7. Persists complete assistant message to database
    8. Emits done event with approval_required payload (if cancel_order was triggered)
    """
    check_rate_limit(request, current_user=current_user)
    clean_message = payload.message.strip()
    if not clean_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty or only whitespace.",
        )

    session_id = payload.session_id.strip() if payload.session_id else str(uuid.uuid4())

    # 1. Persist User Message
    db = SessionLocal()
    try:
        user_record = Message(
            session_id=session_id,
            role="user",
            content=clean_message,
            sources=None,
        )
        db.add(user_record)
        db.commit()
    finally:
        db.close()

    def event_generator() -> Generator[str, None, None]:
        # Emit initial metadata
        yield f"data: {json.dumps({'type': 'meta', 'session_id': session_id})}\n\n"

        # Execute Agent Loop
        agent_res = run_agent(clean_message, user_id=current_user.id)

        # Stream the tokens to the frontend
        words = agent_res.answer.split(" ")
        for i, word in enumerate(words):
            token = word if i == 0 else " " + word
            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"

        # Persist full assistant response
        save_db = SessionLocal()
        try:
            bot_record = Message(
                session_id=session_id,
                role="assistant",
                content=agent_res.answer,
                sources=agent_res.sources,
            )
            save_db.add(bot_record)
            save_db.commit()
        except Exception as e:
            print(f"Error saving assistant message: {e}")
        finally:
            save_db.close()

        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'answer': agent_res.answer, 'sources': agent_res.sources, 'approval_required': agent_res.approval_required})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{session_id}", response_model=List[MessageItem])
def get_session_history(
    session_id: str,
    db: Session = Depends(get_db),
) -> List[MessageItem]:
    """Retrieve full conversation history for a given session."""
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = db.execute(stmt).scalars().all()
    return list(messages)
