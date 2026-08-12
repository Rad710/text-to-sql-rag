"""Schema + round-trip tests for the app datastore (task 0017).

The metadata tests are pure (no DB); the round-trip is an opt-in ``integration`` test against a live
Postgres (``APP_DATABASE_URL``), like the MySQL integration suite.
"""

from __future__ import annotations

import asyncio

import pytest

from app.store.models import Base, Conversation, Feedback, Message, User


def test_schema_defines_the_four_tables() -> None:
    assert {"users", "conversations", "messages", "feedback"} <= set(Base.metadata.tables)


def test_user_columns() -> None:
    cols = {c.name for c in User.__table__.columns}
    assert {"id", "email", "name", "password_hash", "created_at"} <= cols
    assert User.__table__.c.email.unique


def test_foreign_keys_chain_user_conversation_message_feedback() -> None:
    def fk_targets(model: type) -> set[str]:
        return {
            next(iter(c.foreign_keys)).column.table.name
            for c in model.__table__.columns
            if c.foreign_keys
        }

    assert fk_targets(Conversation) == {"users"}
    assert fk_targets(Message) == {"conversations"}
    assert fk_targets(Feedback) == {"messages"}


def test_feedback_is_one_per_message() -> None:
    assert Feedback.__table__.c.message_id.unique


@pytest.mark.integration
def test_store_round_trip() -> None:
    """Insert user → conversation → message → feedback and read it back against a live Postgres."""
    from sqlalchemy import select
    from sqlalchemy.exc import InterfaceError, OperationalError
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.config import get_settings

    url = get_settings().app_database_url

    async def run() -> None:
        engine = create_async_engine(url)
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)

            maker = async_sessionmaker(engine, expire_on_commit=False)
            async with maker() as session:
                user = User(email="a@dyr.test", name="Ana", password_hash="hashed")
                conv = Conversation(user=user, title="rutas")
                msg = Message(conversation=conv, role="user", content="facturación por ruta")
                session.add_all([user, conv, msg, Feedback(message=msg, rating=1)])
                await session.commit()

            async with maker() as session:
                got = (
                    await session.execute(select(User).where(User.email == "a@dyr.test"))
                ).scalar_one()
                assert got.name == "Ana"
                conv_row = (await session.execute(select(Conversation))).scalar_one()
                assert conv_row.user_id == got.id
                msg_row = (await session.execute(select(Message))).scalar_one()
                assert msg_row.conversation_id == conv_row.id and msg_row.content
                fb_row = (await session.execute(select(Feedback))).scalar_one()
                assert fb_row.rating == 1 and fb_row.message_id == msg_row.id

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        finally:
            await engine.dispose()

    try:
        asyncio.run(run())
    except (OSError, InterfaceError, OperationalError) as exc:  # pragma: no cover - env-dependent
        pytest.skip(f"no Postgres reachable at {url}: {exc}")
