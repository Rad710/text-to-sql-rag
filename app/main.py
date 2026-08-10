"""FastAPI application entrypoint.

Task 0001 ships only the skeleton: a health check and a stub ``/chat`` that echoes in mock
mode. The agentic loop, RAG, and SQL execution arrive in later tasks (see docs/tasks/).
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from app import __version__
from app.config import get_settings

app = FastAPI(title="text-to-sql-rag", version=__version__)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    mode: str


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "version": __version__}


@app.post("/chat")
def chat(req: ChatRequest) -> ChatResponse:
    """Stub chat endpoint.

    Returns a deterministic placeholder so the app is runnable end-to-end with no API key.
    The real agentic pipeline replaces this body in task 0008/0009.
    """
    settings = get_settings()
    answer = (
        f"[stub · {settings.llm_mode} mode] received: {req.question!r}. "
        "The agentic text-to-SQL pipeline is not wired yet — see docs/tasks/."
    )
    return ChatResponse(answer=answer, mode=settings.llm_mode)
