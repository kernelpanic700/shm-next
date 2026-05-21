# =============================================================================
# shm-next — Tariff Model
#
# =============================================================================
from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base


class TariffModel(Base):
    """Модель тарифа."""

    __tablename__ = "tariffs"

    id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    services: Mapped[list] = mapped_column(JSON, nullable=False, server_default="[]")
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    price: Mapped[float] = mapped_column(Numeric(precision=12, scale=4), nullable=False, server_default="0")
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default="RUB"
    )
    billing_period: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="monthly"
    )
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="1"
    )

    abonents = relationship("AbonentModel", back_populates="tariff")
    tariff_services = relationship(
        "TariffServiceModel", back_populates="tariff", lazy="dynamic"
    )

    __table_args__ = (
        Index("idx_tariffs_active", "is_active"),
        Index("idx_tariffs_name", "name"),
    )


class TariffServiceModel(Base):
    """Модель услуги тарифа."""

    __tablename__ = "tariff_services"

    id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    tariff_id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tariffs.id"), nullable=False
    )
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default="RUB"
    )
    unit: Mapped[str] = mapped_column(String(20), server_default="day")
    is_optional: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )

    tariff = relationship("TariffModel", back_populates="tariff_services")

    __table_args__ = (
        UniqueConstraint("tariff_id", "service_type", name="uq_tariff_service"),
        Index("idx_tariff_services_type", "service_type"),
    )
