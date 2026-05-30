"""Add tariffs version column.

Revision ID: 009_add_tariffs_version
Revises: 008_create_tariff_services
Create Date: 2026-05-27 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "009_add_tariffs_version"
down_revision: Union[str, None] = "008_create_tariff_services"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("tariffs")}
    if "version" not in columns:
        op.add_column(
            "tariffs",
            sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("tariffs")}
    if "version" in columns:
        op.drop_column("tariffs", "version")
