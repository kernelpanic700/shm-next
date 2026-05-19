# =============================================================================
# shm-next — Abonent Events
# =============================================================================
"""События, связанные с абонентами."""

from __future__ import annotations

from typing import Any

from app.core.domain.events.event import DomainEvent, EventMetadata
from app.core.domain.value_objects.event_type import EventType


class AbonentCreatedEvent(DomainEvent):
    """Абонент создан."""

    def __init__(
        self,
        abonent_id: str,
        full_name: str,
        phone: str,
        account_number: str,
        balance: float,
        currency: str = "RUB",
        tariff_id: str | None = None,
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.ABONENT_CREATED, metadata)
        self.abonent_id = abonent_id
        self.full_name = full_name
        self.phone = phone
        self.account_number = account_number
        self.balance = balance
        self.currency = currency
        self.tariff_id = tariff_id


class AbonentUpdatedEvent(DomainEvent):
    """Абонент обновлён."""

    def __init__(
        self,
        abonent_id: str,
        changes: dict[str, Any],
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.ABONENT_UPDATED, metadata)
        self.abonent_id = abonent_id
        self.changes = changes


class AbonentBlockedEvent(DomainEvent):
    """Абонент заблокирован."""

    def __init__(
        self,
        abonent_id: str,
        reason: str = "",
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.ABONENT_BLOCKED, metadata)
        self.abonent_id = abonent_id
        self.reason = reason


class AbonentActivatedEvent(DomainEvent):
    """Абонент активирован (или повторно активирован после блокировки)."""

    def __init__(
        self,
        abonent_id: str,
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.ABONENT_ACTIVATED, metadata)
        self.abonent_id = abonent_id
