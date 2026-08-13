"""message tool_data — persist assistant tool steps (task 0041)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-13 00:00:00.000000

Adds a nullable JSON column holding each assistant turn's tool steps (the `run_sql` call + its
structured result), so a reloaded conversation rebuilds the SQL step + result table instead of the
prose alone. Nullable — existing rows stay NULL and render prose-only.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("messages", sa.Column("tool_data", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("messages", "tool_data")
