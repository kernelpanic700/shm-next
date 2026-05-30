# =============================================================================
# shm-next - EventActionRule Model
# =============================================================================
from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, BigInteger, Boolean, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class EventActionRuleModel(Base):
    """Модель правила действия по событию услуги."""

    __tablename__ = "event_action_rules"

    id: Mapped[Any] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    service_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    catalog_service_id: Mapped[Any | None] = mapped_column(PG_UUID(as_uuid=True))
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default="50")
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="1"
    )

    __table_args__ = (
        Index("idx_event_action_rules_event", "event_type", "is_enabled"),
        Index("idx_event_action_rules_service_type", "service_type"),
        Index("idx_event_action_rules_catalog", "catalog_service_id"),
    )
