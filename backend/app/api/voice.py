"""Voice API endpoint for ShopEasy customer support (Phase G).

Accepts voice transcripts or audio input, executes the same agent & guardrails pipeline as /api/chat,
and returns the transcript, answer, sources, and any required confirmation approval tokens.
"""

import json
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.runner import run_agent
from app.core.auth import get_current_user
from app.core.guardrails import mask_pii, screen_prompt_injection
from app.core.rate_limit import check_rate_limit
from app.db import get_db
from app.models.message import Message
from app.models.user import User

router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceRequest(BaseModel):
    transcript: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Speech-to-text transcript from user microphone",
    )
    session_id: Optional[str] = Field(
        None, description="Optional existing session ID to continue conversation"
    )


class VoiceResponse(BaseModel):
    session_id: str
    transcript: str
    answer: str
    sources: List[str]
    approval_required: Optional[Dict[str, Any]] = None


@router.post("", response_model=VoiceResponse, status_code=status.HTTP_200_OK)
def process_voice_transcript(
    request: Request,
    payload: VoiceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VoiceResponse:
    """Process a voice transcript through the exact same agent, RAG, and guardrails pipeline.

    1. Enforces rate limiting
    2. Screens for prompt injection / instruction overrides
    3. Masks sensitive customer PII
    4. Loads past conversation history for session
    5. Executes Agent runner (tools, hybrid search, cross-encoder rerank)
    6. Persists messages to database
    7. Returns transcript, answer, sources, and approval tokens
    """
    check_rate_limit(request, current_user=current_user)

    clean_transcript = payload.transcript.strip()
    if not clean_transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voice transcript cannot be empty.",
        )

    session_id = payload.session_id.strip() if payload.session_id else str(uuid.uuid4())

    # 1. Screen for prompt injection
    is_injected, warning_msg = screen_prompt_injection(clean_transcript)
    if is_injected:
        return VoiceResponse(
            session_id=session_id,
            transcript=clean_transcript,
            answer=warning_msg or "Disallowed instruction override detected.",
            sources=[],
        )

    # 2. Mask sensitive PII
    sanitized_transcript = mask_pii(clean_transcript)

    # 3. Load recent conversation history (last 4 messages) for multi-turn context
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(4)
    )
    past_messages = list(reversed(db.execute(stmt).scalars().all()))
    history = [{"role": m.role, "content": m.content} for m in past_messages]

    # 4. Persist User Voice Message
    user_record = Message(
        session_id=session_id,
        role="user",
        content=f"[Voice] {sanitized_transcript}",
        sources=None,
    )
    db.add(user_record)
    db.commit()

    # 5. Run Agent Loop with Tools and Contextual History
    agent_result = run_agent(
        sanitized_transcript,
        user_id=current_user.id,
        conversation_history=history,
    )

    # 6. Persist Assistant Response
    assistant_record = Message(
        session_id=session_id,
        role="assistant",
        content=agent_result.answer,
        sources=agent_result.sources,
    )
    db.add(assistant_record)
    db.commit()

    return VoiceResponse(
        session_id=session_id,
        transcript=sanitized_transcript,
        answer=agent_result.answer,
        sources=agent_result.sources,
        approval_required=agent_result.approval_required,
    )
