"""Auth persistence operations over the app store (async SQLAlchemy).

Covers user register/authenticate plus refresh-token issuance, rotation, and revocation with reuse
detection (decision 0013): each refresh token is one `refresh_tokens` row; rotating revokes the old
`jti` and issues a new one, and presenting an already-revoked `jti` revokes the user's whole family.
"""

from __future__ import annotations

import datetime as dt

import jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import Settings
from app.store.models import RefreshToken, User


class EmailTakenError(Exception):
    """Raised when registering an email that already exists."""


class InvalidRefreshTokenError(Exception):
    """The refresh token is malformed, unknown, or expired."""


class ReuseDetectedError(Exception):
    """An already-revoked (rotated-away) refresh token was replayed — the family is revoked."""


async def register(session: AsyncSession, *, email: str, name: str, password: str) -> User:
    existing = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing is not None:
        raise EmailTakenError(email)
    user = User(email=email, name=name, password_hash=hash_password(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, *, email: str, password: str) -> User | None:
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


async def get_user(session: AsyncSession, user_id: str) -> User | None:
    return await session.get(User, user_id)


async def issue_tokens(
    session: AsyncSession, user_id: str, settings: Settings | None = None
) -> tuple[str, str]:
    """Mint an access + refresh pair, persisting the refresh `jti`. Returns (access, refresh)."""
    access = create_access_token(user_id, settings)
    refresh, jti, expires_at = create_refresh_token(user_id, settings)
    session.add(RefreshToken(jti=jti, user_id=user_id, expires_at=expires_at))
    await session.commit()
    return access, refresh


async def rotate_tokens(
    session: AsyncSession, refresh_token: str, settings: Settings | None = None
) -> tuple[str, str]:
    """Validate + rotate a refresh token. Revokes the presented `jti` and issues a new pair.

    Raises ``ReuseDetectedError`` (and revokes the user's whole family) if the `jti` was already
    revoked — the signature of a stolen, rotated-away token being replayed — and
    ``InvalidRefreshTokenError`` for anything malformed, unknown, or expired.
    """
    try:
        claims = decode_token(refresh_token, "refresh", settings)
    except jwt.InvalidTokenError as exc:
        raise InvalidRefreshTokenError from exc

    row = await session.get(RefreshToken, claims.jti)
    if row is None:
        raise InvalidRefreshTokenError
    if row.revoked_at is not None:
        await revoke_all(session, row.user_id)
        raise ReuseDetectedError
    if row.expires_at <= dt.datetime.now(tz=dt.UTC):
        raise InvalidRefreshTokenError

    row.revoked_at = dt.datetime.now(tz=dt.UTC)
    access = create_access_token(row.user_id, settings)
    new_refresh, jti, expires_at = create_refresh_token(row.user_id, settings)
    session.add(RefreshToken(jti=jti, user_id=row.user_id, expires_at=expires_at))
    await session.commit()
    return access, new_refresh


async def revoke(
    session: AsyncSession, refresh_token: str, settings: Settings | None = None
) -> None:
    """Revoke a single refresh token (logout). A bad/unknown token is a no-op."""
    try:
        claims = decode_token(refresh_token, "refresh", settings)
    except jwt.InvalidTokenError:
        return
    row = await session.get(RefreshToken, claims.jti)
    if row is not None and row.revoked_at is None:
        row.revoked_at = dt.datetime.now(tz=dt.UTC)
        await session.commit()


async def revoke_all(session: AsyncSession, user_id: str) -> None:
    """Revoke every live refresh token for a user (reuse response / logout-everywhere)."""
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=dt.datetime.now(tz=dt.UTC))
    )
    await session.commit()
