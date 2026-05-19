# =============================================================================
# shm-next — Base Domain Event
# =============================================================================
"""
Базовый класс доменных событий.

Каждое событие содержит:
- event_id: Уникальный идентификатор
- event_type: Тип события (для маршрутизации)
- timestamp: Время возникновения
- metadata: Дополнительные метаданные
- correlation_id: Для трейсинга цепочки событий
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.domain.value_objects.event_type import EventType


class EventMetadata:
    """Метаданные события."""

    def __init__(
        self,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        user_id: str | None = None,
        ip_address: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.correlation_id = correlation_id or str(uuid4())
        self.causation_id = causation_id
        self.user_id = user_id
        self.ip_address = ip_address
        self.extra = extra or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "extra": self.extra,
        }


class DomainEvent:
    """
    Базовый класс доменных событий.

    События — это результат произошедших в домене изменений.
    Они неизменяемы после создания.
    """

    def __init__(
        self,
        event_type: EventType,
        metadata: EventMetadata | None = None,
    ) -> None:
        self._event_id = str(uuid4())
        self._event_type = event_type
        self._timestamp = datetime.now(UTC)
        self._metadata = metadata or EventMetadata()

    @property
    def event_id(self) -> str:
        return self._event_id

    @property
    def event_type(self) -> EventType:
        return self._event_type

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def metadata(self) -> EventMetadata:
        return self._metadata

    @property
    def correlation_id(self) -> str:
        return self._metadata.correlation_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self._event_id,
            "event_type": self._event_type.value,
            "timestamp": self._timestamp.isoformat(),
            "metadata": self._metadata.to_dict(),
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"event_id={self._event_id[:8]}..., "
            f"type={self._event_type.value})"
        )
