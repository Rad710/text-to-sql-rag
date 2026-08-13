"""Password hashing (bcrypt) and JWT create/decode (decisions 0009, 0013). Pure — no DB, no network.

Two token kinds share the signing secret but carry a ``type`` claim so a refresh token can never be
used as an access token: a short-lived **access** token (Bearer, ~15 min) and a longer **refresh**
token carrying a ``jti`` (rotated + reuse-detected server-side — see ``auth.service``).
"""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass

import bcrypt
import jwt

from app.config import Settings, get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


@dataclass(frozen=True, slots=True)
class TokenClaims:
    """The validated claims we care about: whose token, which kind, its id, and when it expires."""

    subject: str
    token_type: str
    jti: str | None
    expires_at: dt.datetime


def create_access_token(subject: str, settings: Settings | None = None) -> str:
    s = settings or get_settings()
    now = dt.datetime.now(tz=dt.UTC)
    payload = {
        "sub": subject,
        "type": "access",
        "iat": now,
        "exp": now + dt.timedelta(minutes=s.jwt_access_expiry_min),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def create_refresh_token(
    subject: str, settings: Settings | None = None
) -> tuple[str, str, dt.datetime]:
    """Return ``(token, jti, expires_at)`` — the caller persists the ``jti`` to allow rotation."""
    s = settings or get_settings()
    now = dt.datetime.now(tz=dt.UTC)
    jti = str(uuid.uuid4())
    expires_at = now + dt.timedelta(days=s.jwt_refresh_expiry_days)
    payload = {"sub": subject, "type": "refresh", "jti": jti, "iat": now, "exp": expires_at}
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm), jti, expires_at


def decode_token(
    token: str, expected_type: str = "access", settings: Settings | None = None
) -> TokenClaims:
    """Decode + verify a token, requiring ``expected_type``. Raises ``jwt.InvalidTokenError``."""
    s = settings or get_settings()
    payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise jwt.InvalidTokenError("missing subject")
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"expected a {expected_type} token")
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)):
        raise jwt.InvalidTokenError("missing exp")
    return TokenClaims(
        subject=subject,
        token_type=expected_type,
        jti=payload.get("jti"),
        expires_at=dt.datetime.fromtimestamp(exp, tz=dt.UTC),
    )
