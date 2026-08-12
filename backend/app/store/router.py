"""Conversation-history endpoints — the authenticated user's saved conversations (task 0019)."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.store import conversations as convo
from app.store.engine import get_session
from app.store.models import User

router = APIRouter(prefix="/conversations", tags=["conversations"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


class ConversationSummary(BaseModel):
    id: str
    title: str


class MessageOut(BaseModel):
    id: str
    role: str
    content: str


class ConversationDetail(BaseModel):
    id: str
    title: str
    messages: list[MessageOut]


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(user: CurrentUser, session: Session) -> list[ConversationSummary]:
    rows = await convo.list_conversations(session, user_id=user.id)
    return [ConversationSummary(id=c.id, title=c.title) for c in rows]


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str, user: CurrentUser, session: Session
) -> ConversationDetail:
    conversation = await convo.get_conversation(
        session, user_id=user.id, conversation_id=conversation_id
    )
    if conversation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "conversation not found")
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        messages=[
            MessageOut(id=m.id, role=m.role, content=m.content) for m in conversation.messages
        ],
    )


feedback_router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    message_id: str
    rating: Literal[-1, 1]  # 👎 / 👍


@feedback_router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def submit_feedback(req: FeedbackRequest, user: CurrentUser, session: Session) -> Response:
    ok = await convo.set_feedback(
        session, user_id=user.id, message_id=req.message_id, rating=req.rating
    )
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "message not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
