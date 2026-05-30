"""Create event action rules.

Revision ID: 007_create_event_action_rules
Revises: 006_extend_user_services_for_shm
Create Date: 2026-05-27 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "007_create_event_action_rules"
down_revision: Union[str, None] = "006_extend_user_services_for_shm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_action_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("service_type", sa.String(length=64), nullable=True),
        sa.Column("catalog_service_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("settings", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_event_action_rules_event",
        "event_action_rules",
        ["event_type", "is_enabled"],
    )
    op.create_index(
        "idx_event_action_rules_service_type",
        "event_action_rules",
        ["service_type"],
    )
    op.create_index(
        "idx_event_action_rules_catalog",
        "event_action_rules",
        ["catalog_service_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_event_action_rules_catalog", table_name="event_action_rules")
    op.drop_index("idx_event_action_rules_service_type", table_name="event_action_rules")
    op.drop_index("idx_event_action_rules_event", table_name="event_action_rules")
    op.drop_table("event_action_rules")
