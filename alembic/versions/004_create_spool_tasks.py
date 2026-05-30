"""Create spool_tasks table.

Revision ID: 004_create_spool_tasks
Revises: 003_add_updated_at
Create Date: 2025-01-01 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004_create_spool_tasks"
down_revision: Union[str, None] = "003_add_updated_at"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "spool_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="NEW"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("worker_id", sa.String(length=100), nullable=True),
        sa.Column("execute_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.String(length=2000), nullable=True),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_spool_status", "spool_tasks", ["status"])
    op.create_index("idx_spool_priority", "spool_tasks", ["priority"])
    op.create_index("idx_spool_action_type", "spool_tasks", ["action_type"])


def downgrade() -> None:
    op.drop_table("spool_tasks")
