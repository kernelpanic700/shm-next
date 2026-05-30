# =============================================================================
# shm-next - CatalogService Model
# =============================================================================
from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class CatalogServiceModel(Base):
    """Модель каталожной услуги SHM."""

    __tablename__ = "services"

    id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    legacy_service_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    cost: Mapped[float] = mapped_column(
        Numeric(precision=12, scale=2), nullable=False, server_default="0"
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default="RUB"
    )
    period_cost: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=4), nullable=False, server_default="1"
    )
    category: Mapped[str | None] = mapped_column(String(16), nullable=True)
    children: Mapped[list | None] = mapped_column(JSON, nullable=True)
    next_service_id: Mapped[Any | None] = mapped_column(PG_UUID(as_uuid=True))
    allow_to_order: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    max_count: Mapped[int | None] = mapped_column(Integer)
    question: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    pay_always: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    no_discount: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    description: Mapped[str | None] = mapped_column(String(255))
    pay_in_credit: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_composite: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="1"
    )

    __table_args__ = (
        Index("idx_catalog_services_category", "category"),
        Index("idx_catalog_services_orderable", "allow_to_order", "is_deleted"),
        Index("idx_catalog_services_legacy_id", "legacy_service_id"),
    )
