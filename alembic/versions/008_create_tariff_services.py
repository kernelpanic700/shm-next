"""Create tariff services table.

Revision ID: 008_create_tariff_services
Revises: 007_create_event_action_rules
Create Date: 2026-05-27 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "008_create_tariff_services"
down_revision: Union[str, None] = "007_create_event_action_rules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    if inspector.has_table("tariff_services"):
        return

    op.create_table(
        "tariff_services",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tariff_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("cost", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="RUB"),
        sa.Column("unit", sa.String(length=20), nullable=True, server_default="day"),
        sa.Column("is_optional", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tariff_id"], ["tariffs.id"], name="fk_tariff_services_tariff"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tariff_id", "service_type", name="uq_tariff_service_type"),
    )
    op.create_index("idx_tariff_services_tariff", "tariff_services", ["tariff_id"])


def downgrade() -> None:
    if inspect(op.get_bind()).has_table("tariff_services"):
        op.drop_index("idx_tariff_services_tariff", table_name="tariff_services")
        op.drop_table("tariff_services")
