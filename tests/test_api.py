"""Tests for the FastAPI SSE API (fake service injected; no DB for the unit tests)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import app, get_chat_limiter, get_service
from app.auth.deps import get_current_user
from app.config import RateLimiter
from app.rag.corpus import build_corpus
from app.rag.embeddings import OfflineEmbedder
from app.rag.engine import RagStore
from app.rag.schema import Column, ForeignKey, SchemaInfo, Table
from app.store.conversations import get_recorder
from app.store.models import User


class _NoopRecorder:
    """A ConversationRecorder that persists nothing — keeps the /chat unit tests DB-free (0019)."""

    async def start(self, *, user_id: str, conversation_id: str | None, question: str) -> str:
        return "conv-test"

    async def finish(self, *, conversation_id: str, answer: str) -> str:
        return "msg-test"


def _t(name: str, *cols: str, pk: str, fks: tuple[ForeignKey, ...] = ()) -> Table:
    columns = tuple(Column(c, "int", nullable=False, is_primary_key=(c == pk)) for c in cols)
    return Table(name=name, columns=columns, foreign_keys=fks)


DRIVER = _t("driver", "driver_code", "driver_name", pk="driver_code")
ROUTE = _t("route", "route_code", "origin", "destination", "price", pk="route_code")
SHIPMENT = _t(
    "shipment",
    "shipment_code",
    "driver_code",
    "route_code",
    "price",
    pk="shipment_code",
    fks=(
        ForeignKey("driver_code", "driver", "driver_code"),
        ForeignKey("route_code", "route", "route_code"),
    ),
)
SCHEMA = SchemaInfo(tables=(DRIVER, ROUTE, SHIPMENT))


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    store = RagStore(path=str(tmp_path), embedder=OfflineEmbedder())
    store.sync_corpus(build_corpus(SCHEMA))
    app.dependency_overrides[get_service] = lambda: (store, SCHEMA)
    # Authenticated by default: bypass the JWT dependency with a stub user (0018).
    app.dependency_overrides[get_current_user] = lambda: User(
        id="u1", email="tester@dyr.test", name="Tester", password_hash="x"
    )
    app.dependency_overrides[get_recorder] = lambda: _NoopRecorder()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health() -> None:
    assert TestClient(app).get("/health").json()["status"] == "ok"


def test_chat_streams_sse_events(client: TestClient) -> None:
    resp = client.post("/chat", json={"question": "total freight revenue per route"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    body = resp.text
    # the stream carries tool steps (incl. the generated SQL), the answer, and a done marker
    assert "event: tool_start" in body
    assert "run_sql" in body
    assert "event: answer" in body
    assert "event: done" in body


def test_chat_requires_question(client: TestClient) -> None:
    assert client.post("/chat", json={}).status_code == 422


def test_chat_accepts_conversation_history(client: TestClient) -> None:
    """The /chat contract carries prior turns for multi-turn context (task 0016)."""
    resp = client.post(
        "/chat",
        json={
            "question": "total freight revenue per route",
            "history": [
                {"role": "user", "content": "hola"},
                {"role": "assistant", "content": "¡Hola!"},
            ],
        },
    )
    assert resp.status_code == 200
    assert "event: answer" in resp.text


def test_chat_rejects_bad_history_role(client: TestClient) -> None:
    resp = client.post(
        "/chat",
        json={"question": "x", "history": [{"role": "robot", "content": "hi"}]},
    )
    assert resp.status_code == 422  # role must be user|assistant


def test_chat_requires_auth(tmp_path: Path) -> None:
    """Without the auth override, /chat needs a Bearer token — 401 otherwise (decision 0009)."""
    store = RagStore(path=str(tmp_path), embedder=OfflineEmbedder())
    store.sync_corpus(build_corpus(SCHEMA))
    app.dependency_overrides[get_service] = lambda: (store, SCHEMA)
    try:
        resp = TestClient(app).post("/chat", json={"question": "total revenue per route"})
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_chat_rate_limited_returns_429(client: TestClient) -> None:
    """A per-user /chat limit trips after the budget, returning 429 + Retry-After (0010)."""
    limiter = RateLimiter(per_minute=1)  # one shared instance across requests
    app.dependency_overrides[get_chat_limiter] = lambda: limiter
    q = {"question": "total freight revenue per route"}
    assert client.post("/chat", json=q).status_code == 200  # first: within budget
    resp = client.post("/chat", json=q)  # second: over the per-minute budget
    assert resp.status_code == 429
    assert int(resp.headers["Retry-After"]) > 0


@pytest.mark.integration
def test_chat_end_to_end_live() -> None:
    import pymysql

    import app.api as api
    from app.rag.introspect import introspect_from_settings

    try:
        introspect_from_settings()
    except pymysql.MySQLError as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"no MySQL reachable: {exc}")

    api._service = None  # force a fresh build against the live DB
    app.dependency_overrides.clear()
    # This test exercises the agent against live MySQL, not auth/persistence: stub the authenticated
    # user (0018) + a no-op recorder (0019) so we need no Bearer token and no real user row.
    app.dependency_overrides[get_current_user] = lambda: User(
        id="u1", email="tester@dyr.test", name="Tester", password_hash="x"
    )
    app.dependency_overrides[get_recorder] = lambda: _NoopRecorder()
    try:
        resp = TestClient(app).post("/chat", json={"question": "total freight revenue per route"})
        assert resp.status_code == 200
        assert "event: answer" in resp.text
        assert "run_sql" in resp.text
    finally:
        app.dependency_overrides.clear()
