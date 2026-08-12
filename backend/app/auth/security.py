"""Password hashing (bcrypt) and JWT create/decode (decision 0009). Pure — no DB, no network."""

from __future__ import annotations

import datetime as dt

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


def create_access_token(subject: str, settings: Settings | None = None) -> str:
    s = settings or get_settings()
    now = dt.datetime.now(tz=dt.UTC)
    payload = {"sub": subject, "iat": now, "exp": now + dt.timedelta(minutes=s.jwt_expiry_min)}
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def decode_token(token: str, settings: Settings | None = None) -> str:
    """Return the token's subject (user id), or raise ``jwt.InvalidTokenError``."""
    s = settings or get_settings()
    payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise jwt.InvalidTokenError("missing subject")
    return subject
