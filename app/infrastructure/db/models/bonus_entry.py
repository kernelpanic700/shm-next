# =============================================================================
# shm-next — BonusEntry Model
# =============================================================================
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class BonusEntryModel(Base):
    """Модель бонусной записи."""

    __tablename__ = "bonus_entries"

    id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    abonent_id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="RUB")
    reason: Mapped[str] = mapped_column(String(500), nullable=False, server_default="")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False, server_default="manual")
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="1"
    )

    __table_args__ = (
        Index("idx_bonus_entries_abonent", "abonent_id"),
        Index("idx_bonus_entries_active", "is_active"),
        Index("idx_bonus_entries_expires", "expires_at"),
    )
