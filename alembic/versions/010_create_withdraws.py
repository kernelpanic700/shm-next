"""Create withdraws table.

Revision ID: 010_create_withdraws
Revises: 009_add_tariffs_version
Create Date: 2026-05-27 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "010_create_withdraws"
down_revision: Union[str, None] = "009_add_tariffs_version"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    if inspector.has_table("withdraws"):
        return

    op.create_table(
        "withdraws",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("abonent_id", sa.String(length=36), nullable=False),
        sa.Column("service_id", sa.String(length=36), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=True, server_default="PENDING"),
        sa.Column("strategy", sa.String(length=20), nullable=True, server_default="honest"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(length=2000), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_withdraws_abonent", "withdraws", ["abonent_id"])
    op.create_index("idx_withdraws_status", "withdraws", ["status"])


def downgrade() -> None:
    if inspect(op.get_bind()).has_table("withdraws"):
        op.drop_index("idx_withdraws_status", table_name="withdraws")
        op.drop_index("idx_withdraws_abonent", table_name="withdraws")
        op.drop_table("withdraws")
