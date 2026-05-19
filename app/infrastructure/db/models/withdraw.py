# =============================================================================
# shm-next — Withdraw Model
# =============================================================================
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base


class WithdrawModel(Base):
    """Модель списания."""

    __tablename__ = "withdraws"

    id: Mapped[Any] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    abonent_id: Mapped[Any] = mapped_column(
        String(36), ForeignKey("abonents.id"), nullable=False
    )
    service_id: Mapped[Any] = mapped_column(
        String(36), ForeignKey("user_services.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="PENDING")
    strategy: Mapped[str] = mapped_column(String(20), server_default="honest")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    meta: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="1"
    )

    abonent = relationship("AbonentModel", back_populates="withdraws")
    service = relationship("ServiceModel")

    __table_args__ = (
        Index("idx_withdraws_abonent", "abonent_id"),
        Index("idx_withdraws_status", "status"),
    )
