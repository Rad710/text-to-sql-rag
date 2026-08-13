"""Auth tests (0018): pure hashing/JWT + an opt-in register→login→me flow over live Postgres."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.ext.asyncio import create_async_engine

from app.api import app
from app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import Settings, get_settings
from app.store import engine as store_engine
from app.store.engine import get_session
from app.store.models import Base


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
    claims = decode_token(token, settings=s)
    assert claims.subject == "user-123" and claims.token_type == "access"


def test_jwt_rejects_wrong_secret() -> None:
    token = create_access_token("u", Settings(jwt_secret=_SECRET_A))
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, settings=Settings(jwt_secret=_SECRET_B))


def test_access_and_refresh_tokens_are_not_interchangeable() -> None:
    s = Settings(jwt_secret=_SECRET_A)
    access = create_access_token("u", s)
    refresh, jti, _exp = create_refresh_token("u", s)
    # An access token is rejected where a refresh is expected, and vice versa (the `type` claim).
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(access, "refresh", settings=s)
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(refresh, "access", settings=s)
    claims = decode_token(refresh, "refresh", settings=s)
    assert claims.subject == "u" and claims.jti == jti


def test_register_rejects_invalid_input() -> None:
    """Register validates at the edge (422) before the DB is touched — a bad body never reaches the
    store. Validation runs before the endpoint, so no session is needed (get_session is stubbed)."""

    async def _no_session() -> AsyncIterator[None]:
        yield None  # never used — a 422 short-circuits before the endpoint body runs

    app.dependency_overrides[get_session] = _no_session
    try:
        c = TestClient(app)
        good = {"email": "ok@example.com", "name": "Ok", "password": "longenough1"}
        assert c.post("/auth/register", json={**good, "email": "notanemail"}).status_code == 422
        assert c.post("/auth/register", json={**good, "password": "short"}).status_code == 422
        assert c.post("/auth/register", json={**good, "name": ""}).status_code == 422
        bad_login = c.post("/auth/login", json={"email": "notanemail", "password": "x"})
        assert bad_login.status_code == 422  # login email is validated too
    finally:
        app.dependency_overrides.clear()


@pytest.mark.integration
def test_register_login_me_flow() -> None:
    url = get_settings().app_database_url
    email = f"user-{uuid.uuid4()}@example.com"

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
                "/auth/register", json={"email": email, "name": "Ana", "password": "s3cret!pw"}
            )
            assert reg.status_code == 201 and reg.json()["access_token"]

            dup = await ac.post(
                "/auth/register", json={"email": email, "name": "Ana", "password": "s3cret!pw"}
            )
            assert dup.status_code == 409  # email already registered

            login = await ac.post("/auth/login", json={"email": email, "password": "s3cret!pw"})
            assert login.status_code == 200
            token = login.json()["access_token"]
            refresh = login.json()["refresh_token"]

            bad = await ac.post("/auth/login", json={"email": email, "password": "nopenope1"})
            assert bad.status_code == 401

            me = await ac.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert me.status_code == 200 and me.json()["email"] == email
            assert (await ac.get("/auth/me")).status_code == 401  # no token

            # A refresh token can't be used as a Bearer access token (decision 0013).
            assert (
                await ac.get("/auth/me", headers={"Authorization": f"Bearer {refresh}"})
            ).status_code == 401

            # Rotation: refresh yields a new pair, and the new access token authenticates.
            rot = await ac.post("/auth/refresh", json={"refresh_token": refresh})
            assert rot.status_code == 200
            new_refresh = rot.json()["refresh_token"]
            assert new_refresh != refresh
            new_me = await ac.get(
                "/auth/me", headers={"Authorization": f"Bearer {rot.json()['access_token']}"}
            )
            assert new_me.status_code == 200

            # Reuse detection: replaying the rotated-away refresh token is rejected...
            reuse = await ac.post("/auth/refresh", json={"refresh_token": refresh})
            assert reuse.status_code == 401
            # ...and it revokes the family, so even the new refresh token is now dead.
            assert (
                await ac.post("/auth/refresh", json={"refresh_token": new_refresh})
            ).status_code == 401

            # Logout revokes a live refresh token.
            login2 = await ac.post("/auth/login", json={"email": email, "password": "s3cret!pw"})
            r2 = login2.json()["refresh_token"]
            assert (await ac.post("/auth/logout", json={"refresh_token": r2})).status_code == 204
            assert (await ac.post("/auth/refresh", json={"refresh_token": r2})).status_code == 401

    try:
        asyncio.run(flow())
    except (OSError, InterfaceError, OperationalError) as exc:  # pragma: no cover - env-dependent
        pytest.skip(f"no Postgres reachable: {exc}")
    finally:
        # Drop the app engine bound to this (now-closed) loop so it doesn't leak to other tests.
        store_engine._engine = None
        store_engine._sessionmaker = None
