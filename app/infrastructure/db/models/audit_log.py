# =============================================================================
# shm-next — AuditLog Model
# =============================================================================
from __future__ import annotations

from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class AuditLogModel(Base):
    """Модель аудиторского лога."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True, primary_key=True)
    actor_id: Mapped[Any | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    old_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="1"
    )

    __table_args__ = (
        Index("idx_audit_actor", "actor_id"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
    )
