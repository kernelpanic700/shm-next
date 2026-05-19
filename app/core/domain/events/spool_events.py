# =============================================================================
# shm-next — Spool Events
# =============================================================================
"""События, связанные с очередью внешних действий (Spool)."""

from __future__ import annotations

from app.core.domain.events.event import DomainEvent, EventMetadata
from app.core.domain.value_objects.event_type import EventType


class SpoolTaskCreatedEvent(DomainEvent):
    """Задача внешнего действия создана и помещена в очередь."""

    def __init__(
        self,
        task_id: int,
        action_type: str,
        abonent_id: str | None = None,
        priority: int = 50,
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.SPOOL_TASK_CREATED, metadata)
        self.task_id = task_id
        self.action_type = action_type
        self.abonent_id = abonent_id
        self.priority = priority


class SpoolTaskStartedEvent(DomainEvent):
    """Задача начала выполняться воркером."""

    def __init__(
        self,
        task_id: int,
        worker_id: str,
        action_type: str,
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.SPOOL_TASK_STARTED, metadata)
        self.task_id = task_id
        self.worker_id = worker_id
        self.action_type = action_type


class SpoolTaskCompletedEvent(DomainEvent):
    """Задача успешно завершена."""

    def __init__(
        self,
        task_id: int,
        action_type: str,
        result: dict | None = None,
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.SPOOL_TASK_COMPLETED, metadata)
        self.task_id = task_id
        self.action_type = action_type
        self.result = result


class SpoolTaskFailedEvent(DomainEvent):
    """Задача завершилась с ошибкой."""

    def __init__(
        self,
        task_id: int,
        action_type: str,
        error: str,
        retry_count: int,
        max_retries: int,
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.SPOOL_TASK_FAILED, metadata)
        self.task_id = task_id
        self.action_type = action_type
        self.error = error
        self.retry_count = retry_count
        self.max_retries = max_retries


class SpoolTaskMovedToDLQEvent(DomainEvent):
    """Задача перемещена в Dead Letter Queue."""

    def __init__(
        self,
        task_id: int,
        action_type: str,
        error: str,
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.SPOOL_TASK_DLQ, metadata)
        self.task_id = task_id
        self.action_type = action_type
        self.error = error
