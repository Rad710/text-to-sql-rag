"""Auth tests (0018): pure hashing/JWT + an opt-in register→login→me flow over live Postgres."""

from __future__ import annotations

import asyncio
import uuid

import jwt
import pytest

from app.auth.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import Settings


def test_password_hash_round_trip() -> None:
    h = hash_password("hunter2")
    assert h != "hunter2"  # not stored in the clear
    assert verify_password("hunter2", h)
    assert not verify_password("wrong", h)


# ≥32-byte secrets so PyJWT doesn't emit an InsecureKeyLengthWarning in the test output.
_SECRET_A = "test-secret-aaaaaaaaaaaaaaaaaaaaaaaaaaaa"
_SECRET_B = "test-secret-bbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def test_jwt_round_trip() -> None:
    s = Settings(jwt_secret=_SECRET_A)
    token = create_access_token("user-123", s)
    assert decode_token(token, s) == "user-123"


def test_jwt_rejects_wrong_secret() -> None:
    token = create_access_token("u", Settings(jwt_secret=_SECRET_A))
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, Settings(jwt_secret=_SECRET_B))


@pytest.mark.integration
def test_register_login_me_flow() -> None:
    import os

    import httpx
    from sqlalchemy.exc import InterfaceError, OperationalError
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.api import app
    from app.store import engine as store_engine
    from app.store.models import Base

    url = os.environ.get("APP_DATABASE_URL", "postgresql+asyncpg://app:app@localhost:5432/dyr_app")
    email = f"user-{uuid.uuid4()}@dyr.test"

    async def flow() -> None:
        # Create the schema, then drive the ASGI app in this one loop, so the app's async engine and
        # the requests share it (TestClient uses a fresh loop per request → breaks a global engine).
        schema_engine = create_async_engine(url)
        async with schema_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await schema_engine.dispose()

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            reg = await ac.post(
                "/auth/register", json={"email": email, "name": "Ana", "password": "s3cret!"}
            )
            assert reg.status_code == 201 and reg.json()["access_token"]

            dup = await ac.post(
                "/auth/register", json={"email": email, "name": "Ana", "password": "x"}
            )
            assert dup.status_code == 409  # email already registered

            login = await ac.post("/auth/login", json={"email": email, "password": "s3cret!"})
            assert login.status_code == 200
            token = login.json()["access_token"]

            bad = await ac.post("/auth/login", json={"email": email, "password": "nope"})
            assert bad.status_code == 401

            me = await ac.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert me.status_code == 200 and me.json()["email"] == email
            assert (await ac.get("/auth/me")).status_code == 401  # no token

    try:
        asyncio.run(flow())
    except (OSError, InterfaceError, OperationalError) as exc:  # pragma: no cover - env-dependent
        pytest.skip(f"no Postgres reachable: {exc}")
    finally:
        # Drop the app engine bound to this (now-closed) loop so it doesn't leak to other tests.
        store_engine._engine = None
        store_engine._sessionmaker = None
