"""FastAPI streaming API for the text-to-SQL agent.

`POST /chat` runs the agent and **streams its events over SSE** (tool start → generated SQL →
tool result → answer → usage → done), so the frontend (task 0010) can show the SQL and steps live.
`GET /health` for liveness. The RAG store + schema are built once and cached behind an injectable
dependency, so the endpoint tests without a database.
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Annotated, Literal

import pymysql
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app import __version__
from app.agent import AgentEvent, stream
from app.auth.deps import get_current_user
from app.auth.router import router as auth_router
from app.config import RateLimiter, get_settings
from app.rag.corpus import build_corpus
from app.rag.engine import RagStore
from app.rag.introspect import introspect_from_settings
from app.rag.schema import SchemaInfo
from app.store.conversations import ConversationRecorder, get_recorder
from app.store.models import User
from app.store.router import feedback_router
from app.store.router import router as conversations_router

app = FastAPI(title="text-to-sql-rag", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(feedback_router)

_service: tuple[RagStore, SchemaInfo] | None = None


def get_service() -> tuple[RagStore, SchemaInfo]:
    """Memoized (RAG store, schema), built on first use. 503 if the DB is unavailable."""
    global _service
    if _service is None:
        settings = get_settings()
        try:
            schema = introspect_from_settings()
        except pymysql.MySQLError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Database unavailable — start it with `docker compose up`. ({exc})",
            ) from exc
        store = RagStore(path=settings.chroma_path)
        store.sync_corpus(build_corpus(schema))
        _service = (store, schema)
    return _service


_chat_limiter: RateLimiter | None = None


def get_chat_limiter() -> RateLimiter:
    """Memoized per-user /chat limiter, sized from settings (0010). Overridable in tests."""
    global _chat_limiter
    if _chat_limiter is None:
        s = get_settings()
        _chat_limiter = RateLimiter(per_minute=s.rate_limit_per_min, per_day=s.rate_limit_per_day)
    return _chat_limiter


def enforce_chat_rate_limit(
    user: Annotated[User, Depends(get_current_user)],
    limiter: Annotated[RateLimiter, Depends(get_chat_limiter)],
) -> None:
    """Rate-limit /chat per authenticated user; a denial is a 429 + Retry-After (0010)."""
    result = limiter.check(user.id, time.time())
    if not result.ok:
        # The reason only — the client owns the "retry in N" hint (it has Retry-After), so the two
        # layers don't each repeat "probá de nuevo".
        detail = (
            "Alcanzaste el límite diario de consultas."
            if result.scope == "day"
            else "Demasiadas consultas seguidas."
        )
        raise HTTPException(
            status_code=429,
            detail=detail,
            headers={"Retry-After": str(result.retry_after)},
        )


class Turn(BaseModel):
    """One prior conversation turn (text only) — the agent's tool-call trace is not replayed."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[Turn] = []
    conversation_id: str | None = None
    language: Literal["es", "en"] | None = (
        None  # UI language (task 0040); drives the answer language
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe. Also surfaces the runtime mode so the UI can label it honestly."""
    s = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "llm_mode": s.llm_mode,
        "model": s.llm_model if s.llm_mode == "openai" else "mock",
    }


def _sse(event: AgentEvent) -> str:
    return f"event: {event.type}\ndata: {json.dumps(event.data)}\n\n"


@app.post("/chat")
async def chat(
    req: ChatRequest,
    user: Annotated[User, Depends(get_current_user)],
    recorder: Annotated[ConversationRecorder, Depends(get_recorder)],
    _rate_limit: Annotated[None, Depends(enforce_chat_rate_limit)],
    service: tuple[RagStore, SchemaInfo] = Depends(get_service),
) -> StreamingResponse:
    """Answer a question, streaming the agent's events as SSE. Requires a valid JWT (0009).

    Persists the turn under the user's conversation (0019): the user message before streaming, the
    assistant answer when the stream ends. The agent's context still comes from ``history`` (0016).
    """
    store, schema = service
    history = [turn.model_dump() for turn in req.history]
    conversation_id = await recorder.start(
        user_id=user.id, conversation_id=req.conversation_id, question=req.question
    )

    async def event_stream() -> AsyncIterator[str]:
        yield _sse(AgentEvent("conversation", {"id": conversation_id}))
        answer = ""
        for event in stream(
            req.question, store=store, schema=schema, history=history, language=req.language
        ):
            if event.type == "answer":
                answer = str(event.data.get("text") or "")
            yield _sse(event)
        message_id = await recorder.finish(conversation_id=conversation_id, answer=answer)
        yield _sse(AgentEvent("message", {"id": message_id}))  # UI attaches feedback here (0020)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
