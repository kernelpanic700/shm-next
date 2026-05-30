"""Create invoices table.

Revision ID: 011_create_invoices
Revises: 010_create_withdraws
Create Date: 2026-05-27 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "011_create_invoices"
down_revision: Union[str, None] = "010_create_withdraws"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    if inspector.has_table("invoices"):
        return

    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("abonent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="RUB"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["abonent_id"], ["abonents.id"], name="fk_invoices_abonent"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_invoices_abonent", "invoices", ["abonent_id"])
    op.create_index("idx_invoices_status", "invoices", ["status"])
    op.create_index("idx_invoices_due_date", "invoices", ["due_date"])


def downgrade() -> None:
    if inspect(op.get_bind()).has_table("invoices"):
        op.drop_index("idx_invoices_due_date", table_name="invoices")
        op.drop_index("idx_invoices_status", table_name="invoices")
        op.drop_index("idx_invoices_abonent", table_name="invoices")
        op.drop_table("invoices")
