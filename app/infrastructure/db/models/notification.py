# =============================================================================
# shm-next — Notification Model
#
# =============================================================================
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base


class NotificationModel(Base):
    """Модель уведомления."""

    __tablename__ = "notifications"

    id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    abonent_id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("abonents.id"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="PENDING")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="1"
    )

    abonent = relationship("AbonentModel", back_populates="notifications")

    __table_args__ = (
        Index("idx_notifications_abonent", "abonent_id"),
        Index("idx_notifications_status", "status"),
    )
