"""Conversation + message persistence over the app store (task 0019)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.store.engine import get_sessionmaker
from app.store.models import Conversation, Message

_DEFAULT_TITLE = "Nueva conversación"


async def resolve_conversation(
    session: AsyncSession, *, user_id: str, conversation_id: str | None, question: str
) -> Conversation:
    """Return the user's conversation (if owned) or create a new one titled from the question."""
    if conversation_id:
        existing = (
            await session.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id, Conversation.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing
    title = question.strip()[:80] or _DEFAULT_TITLE
    conversation = Conversation(user_id=user_id, title=title)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def save_message(
    session: AsyncSession, *, conversation_id: str, role: str, content: str
) -> None:
    session.add(Message(conversation_id=conversation_id, role=role, content=content))
    await session.commit()


async def list_conversations(session: AsyncSession, *, user_id: str) -> list[Conversation]:
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
    )
    return list(result.scalars().all())


async def get_conversation(
    session: AsyncSession, *, user_id: str, conversation_id: str
) -> Conversation | None:
    """A conversation with its messages eager-loaded, only if owned by the user (else None)."""
    result = await session.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .options(selectinload(Conversation.messages))
    )
    return result.scalar_one_or_none()


class ConversationRecorder:
    """Persists a chat turn. Injected into ``/chat`` (Depends) so unit tests can swap a no-op."""

    async def start(self, *, user_id: str, conversation_id: str | None, question: str) -> str:
        """Resolve/create the conversation, save the user message, return the conversation id."""
        async with get_sessionmaker()() as session:
            conversation = await resolve_conversation(
                session, user_id=user_id, conversation_id=conversation_id, question=question
            )
            cid = conversation.id
            await save_message(session, conversation_id=cid, role="user", content=question)
        return cid

    async def finish(self, *, conversation_id: str, answer: str) -> None:
        async with get_sessionmaker()() as session:
            await save_message(
                session, conversation_id=conversation_id, role="assistant", content=answer
            )


def get_recorder() -> ConversationRecorder:
    return ConversationRecorder()
