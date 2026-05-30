"""Extend user services for SHM lifecycle.

Revision ID: 006_extend_user_services_for_shm
Revises: 005_create_catalog_services
Create Date: 2026-05-27 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

revision: str = "006_extend_user_services_for_shm"
down_revision: Union[str, None] = "005_create_catalog_services"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("user_services"):
        op.create_table(
            "user_services",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("abonent_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("service_type", sa.String(length=50), nullable=False),
            sa.Column("tariff_service_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("catalog_service_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="INIT"),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expire_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="RUB"),
            sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column("period_cost", sa.Numeric(precision=10, scale=4), nullable=False, server_default="1"),
            sa.Column("next_service_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("auto_bill", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("pay_always", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("pay_in_credit", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("no_discount", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["abonent_id"], ["abonents.id"], name="fk_user_services_abonent"),
            sa.ForeignKeyConstraint(["catalog_service_id"], ["services.id"], name="fk_user_services_catalog_service"),
            sa.ForeignKeyConstraint(["parent_id"], ["user_services.id"], name="fk_user_services_parent", ondelete="SET NULL"),
        )
    else:
        existing_columns = {column["name"] for column in inspector.get_columns("user_services")}
        columns = [
            sa.Column("catalog_service_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("expire_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("period_cost", sa.Numeric(precision=10, scale=4), nullable=False, server_default="1"),
            sa.Column("next_service_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("auto_bill", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("pay_always", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("pay_in_credit", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("no_discount", sa.Boolean(), nullable=False, server_default="false"),
        ]
        for column in columns:
            if column.name not in existing_columns:
                op.add_column("user_services", column)

        existing_fks = {fk["name"] for fk in inspector.get_foreign_keys("user_services")}
        if "fk_user_services_catalog_service" not in existing_fks:
            op.create_foreign_key("fk_user_services_catalog_service", "user_services", "services", ["catalog_service_id"], ["id"])
        if "fk_user_services_parent" not in existing_fks:
            op.create_foreign_key("fk_user_services_parent", "user_services", "user_services", ["parent_id"], ["id"], ondelete="SET NULL")

    existing_indexes = {index["name"] for index in inspect(op.get_bind()).get_indexes("user_services")}
    if "idx_services_abonent" not in existing_indexes:
        op.create_index("idx_services_abonent", "user_services", ["abonent_id"])
    if "idx_services_catalog" not in existing_indexes:
        op.create_index("idx_services_catalog", "user_services", ["catalog_service_id"])
    if "idx_services_expire" not in existing_indexes:
        op.create_index("idx_services_expire", "user_services", ["expire_at"])
    if "idx_services_parent" not in existing_indexes:
        op.create_index("idx_services_parent", "user_services", ["parent_id"])
    if "idx_services_status" not in existing_indexes:
        op.create_index("idx_services_status", "user_services", ["status"])
    if "idx_services_type" not in existing_indexes:
        op.create_index("idx_services_type", "user_services", ["service_type"])


def downgrade() -> None:
    if inspect(op.get_bind()).has_table("user_services"):
        op.drop_table("user_services")
