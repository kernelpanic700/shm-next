"""extend abonent profiles and storage

Revision ID: 014_abonent_profiles_storage
Revises: 013_create_automation_settings
Create Date: 2026-05-31
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "014_abonent_profiles_storage"
down_revision: str | None = "013_create_automation_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("abonents", sa.Column("login", sa.String(length=128), nullable=True))
    op.add_column("abonents", sa.Column("login2", sa.String(length=128), nullable=True))
    op.add_column("abonents", sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("abonents", sa.Column("discount", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"))
    op.add_column("abonents", sa.Column("credit", sa.Numeric(precision=12, scale=4), nullable=False, server_default="0"))
    op.add_column("abonents", sa.Column("bonus", sa.Numeric(precision=12, scale=4), nullable=False, server_default="0"))
    op.add_column("abonents", sa.Column("comment", sa.Text(), nullable=True))
    op.add_column("abonents", sa.Column("contract", sa.String(length=32), nullable=True))
    op.add_column("abonents", sa.Column("can_overdraft", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("abonents", sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("abonents", sa.Column("settings", sa.JSON(), nullable=True))
    op.create_unique_constraint("uq_abonents_login", "abonents", ["login"])
    op.create_unique_constraint("uq_abonents_login2", "abonents", ["login2"])
    op.create_foreign_key("fk_abonents_partner", "abonents", "abonents", ["partner_id"], ["id"])
    op.create_index("idx_abonents_partner", "abonents", ["partner_id"])

    op.execute("UPDATE abonents SET login = phone WHERE login IS NULL")
    op.execute("UPDATE abonents SET login2 = email WHERE login2 IS NULL AND email IS NOT NULL")
    op.execute("UPDATE abonents SET contract = account_number WHERE contract IS NULL")
    op.execute("UPDATE abonents SET settings = '{}'::json WHERE settings IS NULL")

    op.create_table(
        "abonent_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("abonent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("abonents.id"), nullable=False, unique=True),
        sa.Column("data", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "abonent_storage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("abonent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("abonents.id"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("user_service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=True),
        sa.Column("data", sa.LargeBinary(length=16 * 1024 * 1024), nullable=True),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("content_type", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("abonent_id", "name", name="uq_abonent_storage_abonent_name"),
    )
    op.create_index("idx_abonent_storage_service", "abonent_storage", ["user_service_id"])


def downgrade() -> None:
    op.drop_index("idx_abonent_storage_service", table_name="abonent_storage")
    op.drop_table("abonent_storage")
    op.drop_table("abonent_profiles")
    op.drop_index("idx_abonents_partner", table_name="abonents")
    op.drop_constraint("fk_abonents_partner", "abonents", type_="foreignkey")
    op.drop_constraint("uq_abonents_login2", "abonents", type_="unique")
    op.drop_constraint("uq_abonents_login", "abonents", type_="unique")
    op.drop_column("abonents", "settings")
    op.drop_column("abonents", "verified")
    op.drop_column("abonents", "can_overdraft")
    op.drop_column("abonents", "contract")
    op.drop_column("abonents", "comment")
    op.drop_column("abonents", "bonus")
    op.drop_column("abonents", "credit")
    op.drop_column("abonents", "discount")
    op.drop_column("abonents", "partner_id")
    op.drop_column("abonents", "login2")
    op.drop_column("abonents", "login")
