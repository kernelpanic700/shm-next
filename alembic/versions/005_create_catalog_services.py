"""Create SHM catalog services.

Revision ID: 005_create_catalog_services
Revises: 004_create_spool_tasks
Create Date: 2026-05-27 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005_create_catalog_services"
down_revision: Union[str, None] = "004_create_spool_tasks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("legacy_service_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("cost", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="RUB"),
        sa.Column("period_cost", sa.Numeric(precision=10, scale=4), nullable=False, server_default="1"),
        sa.Column("category", sa.String(length=16), nullable=True),
        sa.Column("children", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("next_service_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("allow_to_order", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("max_count", sa.Integer(), nullable=True),
        sa.Column("question", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("pay_always", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("no_discount", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("pay_in_credit", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("config", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("is_composite", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("legacy_service_id"),
    )
    op.create_index("idx_catalog_services_category", "services", ["category"])
    op.create_index(
        "idx_catalog_services_orderable",
        "services",
        ["allow_to_order", "is_deleted"],
    )
    op.create_index("idx_catalog_services_legacy_id", "services", ["legacy_service_id"])


def downgrade() -> None:
    op.drop_index("idx_catalog_services_legacy_id", table_name="services")
    op.drop_index("idx_catalog_services_orderable", table_name="services")
    op.drop_index("idx_catalog_services_category", table_name="services")
    op.drop_table("services")
