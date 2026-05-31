# =============================================================================
# shm-next — Abonent Model
# =============================================================================
from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    JSON,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
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
    login: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    login2: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    account_number: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=True
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
    partner_id: Mapped[Any | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("abonents.id"), nullable=True
    )
    discount: Mapped[float] = mapped_column(Numeric(precision=5, scale=2), nullable=False, server_default="0")
    credit: Mapped[float] = mapped_column(Numeric(precision=12, scale=4), nullable=False, server_default="0")
    bonus: Mapped[float] = mapped_column(Numeric(precision=12, scale=4), nullable=False, server_default="0")
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    contract: Mapped[str | None] = mapped_column(String(32), nullable=True)
    can_overdraft: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
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
    profile = relationship("AbonentProfileModel", back_populates="abonent", uselist=False)
    storage_items = relationship(
        "AbonentStorageModel", back_populates="abonent", lazy="dynamic"
    )
    notifications = relationship(
        "NotificationModel", back_populates="abonent", lazy="dynamic"
    )

    __table_args__ = (
        Index("idx_abonents_status", "status"),
        Index("idx_abonents_balance", "balance"),
        Index("idx_abonents_account", "account_number"),
        Index("idx_abonents_partner", "partner_id"),
    )


class AbonentProfileModel(Base):
    """SHM-style JSON profile attached to an abonent."""

    __tablename__ = "abonent_profiles"

    id: Mapped[Any] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    abonent_id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("abonents.id"), nullable=False, unique=True
    )
    data: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")

    abonent = relationship("AbonentModel", back_populates="profile")


class AbonentStorageModel(Base):
    """Per-abonent key/value storage compatible with SHM storage semantics."""

    __tablename__ = "abonent_storage"

    id: Mapped[Any] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    abonent_id: Mapped[Any] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("abonents.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    user_service_id: Mapped[Any | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("services.id"), nullable=True)
    data: Mapped[bytes | None] = mapped_column(LargeBinary(length=16 * 1024 * 1024), nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)

    abonent = relationship("AbonentModel", back_populates="storage_items")

    __table_args__ = (
        UniqueConstraint("abonent_id", "name", name="uq_abonent_storage_abonent_name"),
        Index("idx_abonent_storage_service", "user_service_id"),
    )
