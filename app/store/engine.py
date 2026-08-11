"""Async SQLAlchemy engine + session for the app datastore (decision 0008).

Lazily created from ``Settings.app_database_url`` so importing the store never opens a connection.
FastAPI routes depend on :func:`get_session`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    global _engine
    if _engine is None:
        url = (settings or get_settings()).app_database_url
        _engine = create_async_engine(url, pool_pre_ping=True)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: an async session, committed on clean exit, rolled back on error."""
    async with get_sessionmaker()() as session:
        yield session
