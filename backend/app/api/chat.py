"""Chat API endpoints for ShopEasy customer support."""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.message import Message
from app.rag.answer import answer_question

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(
        ..., min_length=1, max_length=2000, description="Customer question or message"
    )
    session_id: Optional[str] = Field(
        None, description="Optional existing session ID to continue a conversation"
    )


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[str]


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
    payload: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Process a customer question through the RAG pipeline and persist conversation history.

    - Validates message input
    - Assigns or reuses a session_id
    - Saves the user's message to the messages table
    - Runs vector retrieval and grounded answering
    - Saves the assistant's response and cited sources to the messages table
    - Returns the answer, cited sources, and session_id
    """
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

    # 3. Generate Grounded Answer via RAG Pipeline
    result = answer_question(clean_message)

    # 4. Persist Assistant Response with Cited Sources
    assistant_record = Message(
        session_id=session_id,
        role="assistant",
        content=result.answer,
        sources=result.sources,
    )
    db.add(assistant_record)
    db.commit()

    return ChatResponse(
        session_id=session_id,
        answer=result.answer,
        sources=result.sources,
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
