# =============================================================================
# shm-next — Service Model
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
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base


class ServiceModel(Base):
    """Модель услуги абонента."""

    __tablename__ = "user_services"

    id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    abonent_id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("abonents.id"), nullable=False
    )
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    tariff_service_id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="INIT")
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cost: Mapped[float] = mapped_column(Numeric(precision=12, scale=4), nullable=False, server_default="0")
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default="RUB"
    )
    meta: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="1"
    )

    abonent = relationship("AbonentModel", back_populates="services")

    __table_args__ = (
        Index("idx_services_abonent", "abonent_id"),
        Index("idx_services_status", "status"),
        Index("idx_services_type", "service_type"),
    )
