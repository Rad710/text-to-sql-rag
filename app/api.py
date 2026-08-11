"""FastAPI streaming API for the text-to-SQL agent.

`POST /chat` runs the agent and **streams its events over SSE** (tool start → generated SQL →
tool result → answer → usage → done), so the frontend (task 0010) can show the SQL and steps live.
`GET /health` for liveness. The RAG store + schema are built once and cached behind an injectable
dependency, so the endpoint tests without a database.
"""

from __future__ import annotations

import json
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
from app.config import get_settings
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


class Turn(BaseModel):
    """One prior conversation turn (text only) — the agent's tool-call trace is not replayed."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[Turn] = []
    conversation_id: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "version": __version__}


def _sse(event: AgentEvent) -> str:
    return f"event: {event.type}\ndata: {json.dumps(event.data)}\n\n"


@app.post("/chat")
async def chat(
    req: ChatRequest,
    user: Annotated[User, Depends(get_current_user)],
    recorder: Annotated[ConversationRecorder, Depends(get_recorder)],
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
        for event in stream(req.question, store=store, schema=schema, history=history):
            if event.type == "answer":
                answer = str(event.data.get("text") or "")
            yield _sse(event)
        message_id = await recorder.finish(conversation_id=conversation_id, answer=answer)
        yield _sse(AgentEvent("message", {"id": message_id}))  # UI attaches feedback here (0020)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
