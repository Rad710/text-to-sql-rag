"""FastAPI streaming API for the text-to-SQL agent.

`POST /chat` runs the agent and **streams its events over SSE** (tool start → generated SQL →
tool result → answer → usage → done), so the frontend (task 0010) can show the SQL and steps live.
`GET /health` for liveness. The RAG store + schema are built once and cached behind an injectable
dependency, so the endpoint tests without a database.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
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
from app.store.models import User

app = FastAPI(title="text-to-sql-rag", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)

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


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "version": __version__}


def _sse(event: AgentEvent) -> str:
    return f"event: {event.type}\ndata: {json.dumps(event.data)}\n\n"


@app.post("/chat")
def chat(
    req: ChatRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: tuple[RagStore, SchemaInfo] = Depends(get_service),
) -> StreamingResponse:
    """Answer a question, streaming the agent's events as SSE. Requires a valid JWT (0009)."""
    store, schema = service

    history = [turn.model_dump() for turn in req.history]

    def event_stream() -> Iterator[str]:
        for event in stream(req.question, store=store, schema=schema, history=history):
            yield _sse(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
