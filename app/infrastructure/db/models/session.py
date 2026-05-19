# =============================================================================
# shm-next — Session Model
# =============================================================================
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base


class SessionModel(Base):
    """Модель пользовательской сессии."""

    __tablename__ = "sessions"

    id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    abonent_id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("abonents.id"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="1"
    )

    abonent = relationship("AbonentModel", back_populates="sessions")

    __table_args__ = (
        Index("idx_sessions_abonent", "abonent_id"),
        Index("idx_sessions_expires", "expires_at"),
        Index("idx_sessions_active", "is_active"),
    )
