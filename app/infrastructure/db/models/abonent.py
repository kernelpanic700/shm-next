# =============================================================================
# shm-next — Abonent Model
#
# =============================================================================
from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base


class AbonentModel(Base):
    """Модель абонента."""

    __tablename__ = "abonents"

    id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    account_number: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True
    )
    balance: Mapped[float] = mapped_column(Numeric(precision=12, scale=4), nullable=False, server_default="0")
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default="RUB"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="ACTIVE"
    )
    allow_negative: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    tariff_id: Mapped[Any | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tariffs.id"), nullable=True
    )
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="1"
    )

    tariff = relationship("TariffModel", back_populates="abonents")
    services = relationship("ServiceModel", back_populates="abonent", lazy="dynamic")
    payments = relationship("PaymentModel", back_populates="abonent", lazy="dynamic")
    withdraws = relationship("WithdrawModel", back_populates="abonent", lazy="dynamic")
    sessions = relationship("SessionModel", back_populates="abonent", lazy="dynamic")
    invoices = relationship("InvoiceModel", back_populates="abonent", lazy="dynamic")
    notifications = relationship(
        "NotificationModel", back_populates="abonent", lazy="dynamic"
    )

    __table_args__ = (
        Index("idx_abonents_status", "status"),
        Index("idx_abonents_balance", "balance"),
        Index("idx_abonents_account", "account_number"),
    )
