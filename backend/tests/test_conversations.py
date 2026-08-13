"""Conversation persistence + history endpoints (0019) — opt-in integration over live Postgres."""

from __future__ import annotations

import asyncio
import tempfile
import uuid

import httpx
import pytest
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.ext.asyncio import create_async_engine

import app.store.engine as store_engine
from app.api import app, get_service
from app.config import get_settings
from app.rag.corpus import build_corpus
from app.rag.embeddings import OfflineEmbedder
from app.rag.engine import RagStore
from app.rag.schema import Column, SchemaInfo, Table
from app.store.models import Base


def _schema() -> SchemaInfo:
    cols = (
        Column("route_code", "int", nullable=False, is_primary_key=True),
        Column("price", "int", nullable=False, is_primary_key=False),
    )
    return SchemaInfo(tables=(Table(name="route", columns=cols, foreign_keys=()),))


@pytest.mark.integration
def test_chat_persists_and_history_is_isolated_per_user() -> None:
    url = get_settings().app_database_url
    schema = _schema()
    store = RagStore(path=tempfile.mkdtemp(), embedder=OfflineEmbedder())
    store.sync_corpus(build_corpus(schema))
    app.dependency_overrides[get_service] = lambda: (store, schema)

    async def flow() -> None:
        engine = create_async_engine(url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:

            async def token_for(email: str) -> str:
                r = await ac.post(
                    "/auth/register", json={"email": email, "name": "U", "password": "pw123456"}
                )
                assert r.status_code == 201
                return str(r.json()["access_token"])

            auth_a = {"Authorization": f"Bearer {await token_for(f'a-{uuid.uuid4()}@example.com')}"}
            auth_b = {"Authorization": f"Bearer {await token_for(f'b-{uuid.uuid4()}@example.com')}"}

            chat = await ac.post(
                "/chat", json={"question": "facturación total por ruta"}, headers=auth_a
            )
            assert chat.status_code == 200 and "event: conversation" in chat.text

            listed = await ac.get("/conversations", headers=auth_a)
            assert listed.status_code == 200 and len(listed.json()) == 1
            conv_id = listed.json()[0]["id"]

            detail = await ac.get(f"/conversations/{conv_id}", headers=auth_a)
            assert detail.status_code == 200
            messages = detail.json()["messages"]
            roles = [m["role"] for m in messages]
            assert "user" in roles and "assistant" in roles and len(roles) >= 2
            # The assistant turn persists its tool steps so a reload rebuilds the SQL step + table
            # instead of the prose alone (task 0041). User turns carry no tool_data.
            assistant = next(m for m in messages if m["role"] == "assistant")
            assert assistant["tool_data"] and any(
                s["name"] == "run_sql" for s in assistant["tool_data"]
            )
            assert next(m for m in messages if m["role"] == "user")["tool_data"] is None

            # feedback on the assistant message (task 0020): upsert, owner-checked, validated
            msg_id = next(m["id"] for m in messages if m["role"] == "assistant")
            up = await ac.post(
                "/feedback", json={"message_id": msg_id, "rating": 1}, headers=auth_a
            )
            assert up.status_code == 204
            re_rate = await ac.post(
                "/feedback", json={"message_id": msg_id, "rating": -1}, headers=auth_a
            )
            assert re_rate.status_code == 204  # idempotent upsert (one per message)
            cross = await ac.post(
                "/feedback", json={"message_id": msg_id, "rating": 1}, headers=auth_b
            )
            assert cross.status_code == 404  # not user B's message
            bad = await ac.post(
                "/feedback", json={"message_id": msg_id, "rating": 5}, headers=auth_a
            )
            assert bad.status_code == 422  # rating must be -1|1

            # user B cannot see user A's conversation, and has none of their own
            assert (await ac.get(f"/conversations/{conv_id}", headers=auth_b)).status_code == 404
            assert (await ac.get("/conversations", headers=auth_b)).json() == []

    try:
        asyncio.run(flow())
    except (OSError, InterfaceError, OperationalError) as exc:  # pragma: no cover - env-dependent
        pytest.skip(f"no Postgres reachable: {exc}")
    finally:
        app.dependency_overrides.clear()
        store_engine._engine = None
        store_engine._sessionmaker = None
