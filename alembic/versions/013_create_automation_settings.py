"""create automation settings

Revision ID: 013_create_automation_settings
Revises: 012_bonus_discounts
Create Date: 2026-05-30
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013_create_automation_settings"
down_revision: str | None = "012_bonus_discounts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ssh_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("public_key", sa.Text(), nullable=True),
        sa.Column("private_key", sa.Text(), nullable=False),
        sa.Column("passphrase", sa.Text(), nullable=True),
        sa.Column("fingerprint", sa.String(length=128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "server_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("transport", sa.String(length=32), nullable=False, server_default="ssh"),
        sa.Column("strategy", sa.String(length=32), nullable=False, server_default="round_robin"),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "command_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("transport", sa.String(length=32), nullable=False, server_default="ssh"),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "servers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("server_groups.id"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False, server_default="22"),
        sa.Column("key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ssh_keys.id"), nullable=True),
        sa.Column("proxy_jump", sa.String(length=255), nullable=True),
        sa.Column("default_cmd", sa.Text(), nullable=True),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.add_column("event_action_rules", sa.Column("server_group_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("event_action_rules", sa.Column("server_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("event_action_rules", sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("event_action_rules", sa.Column("command", sa.Text(), nullable=True))
    op.create_foreign_key("fk_event_action_rules_server_group", "event_action_rules", "server_groups", ["server_group_id"], ["id"])
    op.create_foreign_key("fk_event_action_rules_server", "event_action_rules", "servers", ["server_id"], ["id"])
    op.create_foreign_key("fk_event_action_rules_template", "event_action_rules", "command_templates", ["template_id"], ["id"])
    op.create_index("idx_event_action_rules_server_group", "event_action_rules", ["server_group_id"])


def downgrade() -> None:
    op.drop_index("idx_event_action_rules_server_group", table_name="event_action_rules")
    op.drop_constraint("fk_event_action_rules_template", "event_action_rules", type_="foreignkey")
    op.drop_constraint("fk_event_action_rules_server", "event_action_rules", type_="foreignkey")
    op.drop_constraint("fk_event_action_rules_server_group", "event_action_rules", type_="foreignkey")
    op.drop_column("event_action_rules", "command")
    op.drop_column("event_action_rules", "template_id")
    op.drop_column("event_action_rules", "server_id")
    op.drop_column("event_action_rules", "server_group_id")
    op.drop_table("servers")
    op.drop_table("command_templates")
    op.drop_table("server_groups")
    op.drop_table("ssh_keys")
