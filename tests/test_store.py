"""Pure schema tests for the app datastore models — no database required (task 0017)."""

from __future__ import annotations

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
