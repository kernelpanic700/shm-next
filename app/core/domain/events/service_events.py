# =============================================================================
# shm-next — Service Events
# =============================================================================
"""События активации/деактивации услуг."""

from __future__ import annotations

from app.core.domain.events.event import DomainEvent, EventMetadata
from app.core.domain.value_objects.event_type import EventType


class ServiceActivatedEvent(DomainEvent):
    """Услуга активирована для абонента."""

    def __init__(
        self,
        abonent_id: str,
        service_id: str,
        service_type: str,
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.SERVICE_ACTIVATED, metadata)
        self.abonent_id = abonent_id
        self.service_id = service_id
        self.service_type = service_type


class ServiceDeactivatedEvent(DomainEvent):
    """Услуга деактивирована для абонента."""

    def __init__(
        self,
        abonent_id: str,
        service_id: str,
        service_type: str,
        reason: str = "",
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.SERVICE_DEACTIVATED, metadata)
        self.abonent_id = abonent_id
        self.service_id = service_id
        self.service_type = service_type
        self.reason = reason


class ServiceErrorEvent(DomainEvent):
    """Ошибка при обработке услуги."""

    def __init__(
        self,
        abonent_id: str,
        service_id: str,
        service_type: str,
        error: str,
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.SERVICE_ERROR, metadata)
        self.abonent_id = abonent_id
        self.service_id = service_id
        self.service_type = service_type
        self.error = error
