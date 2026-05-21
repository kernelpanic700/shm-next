# =============================================================================
# shm-next — SpoolTask Model
#
# =============================================================================
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class SpoolTaskModel(Base):
    """Модель задачи внешнего действия."""

    __tablename__ = "spool_tasks"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default="50")
    status: Mapped[str] = mapped_column(String(20), server_default="NEW")
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    execute_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="1"
    )

    __table_args__ = (
        Index("idx_spool_status", "status"),
        Index("idx_spool_priority", "priority"),
        Index("idx_spool_action_type", "action_type"),
    )
