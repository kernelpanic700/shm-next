"""Create bonus entries and discounts tables.

Revision ID: 012_bonus_discounts
Revises: 011_create_invoices
Create Date: 2026-05-28 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "012_bonus_discounts"
down_revision: Union[str, None] = "011_create_invoices"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())

    if not inspector.has_table("bonus_entries"):
        op.create_table(
            "bonus_entries",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("abonent_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("amount", sa.Numeric(precision=12, scale=4), nullable=False),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="RUB"),
            sa.Column("reason", sa.String(length=500), nullable=False, server_default=""),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("source", sa.String(length=50), nullable=False, server_default="manual"),
            sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["abonent_id"], ["abonents.id"], name="fk_bonus_entries_abonent"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("idx_bonus_entries_abonent", "bonus_entries", ["abonent_id"])
        op.create_index("idx_bonus_entries_active", "bonus_entries", ["is_active"])
        op.create_index("idx_bonus_entries_expires", "bonus_entries", ["expires_at"])

    if not inspector.has_table("discounts"):
        op.create_table(
            "discounts",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=2000), nullable=False, server_default=""),
            sa.Column("discount_type", sa.String(length=20), nullable=False, server_default="percent"),
            sa.Column("value", sa.Numeric(precision=12, scale=4), nullable=False),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="RUB"),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("max_uses", sa.Integer(), nullable=True),
            sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("idx_discounts_active", "discounts", ["is_active"])
        op.create_index("idx_discounts_type", "discounts", ["discount_type"])


def downgrade() -> None:
    inspector = inspect(op.get_bind())

    if inspector.has_table("discounts"):
        op.drop_index("idx_discounts_type", table_name="discounts")
        op.drop_index("idx_discounts_active", table_name="discounts")
        op.drop_table("discounts")

    if inspector.has_table("bonus_entries"):
        op.drop_index("idx_bonus_entries_expires", table_name="bonus_entries")
        op.drop_index("idx_bonus_entries_active", table_name="bonus_entries")
        op.drop_index("idx_bonus_entries_abonent", table_name="bonus_entries")
        op.drop_table("bonus_entries")
