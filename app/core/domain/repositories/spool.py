# =============================================================================
# shm-next — Spool Repository Protocol
# =============================================================================
"""Протокол репозитория задач внешних действий."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.infrastructure.db.models import SpoolTaskModel


class SpoolRepositoryProtocol(ABC):
    """Протокол репозитория задач (Spool)."""

    @abstractmethod
    async def create_task(
        self,
        action_type: str,
        payload: dict,
        priority: int = 50,
        max_retries: int = 3,
        execute_after: datetime | None = None,
    ) -> UUID:
        """Создать задачу."""
        ...

    @abstractmethod
    async def get_pending(
        self,
        action_types: list[str] | None = None,
        limit: int = 100,
    ) -> list:
        """Получить задачи, ожидающие выполнения."""
        ...

    @abstractmethod
    async def get_by_id(self, task_id: int) -> SpoolTaskModel | None:
        """Получить задачу по ID."""
        ...

    @abstractmethod
    async def mark_processing(self, task_id: UUID, worker_id: str) -> bool:
        """Отметить задачу как выполняемую."""
        ...

    @abstractmethod
    async def mark_completed(self, task_id: UUID, result: dict | None = None) -> bool:
        """Отметить задачу как завершённую."""
        ...

    @abstractmethod
    async def mark_failed(
        self, task_id: UUID, error: str, retry_count: int
    ) -> bool:
        """Отметить задачу как неудачную."""
        ...

    @abstractmethod
    async def move_to_dlq(self, task_id: UUID, error: str) -> bool:
        """Переместить задачу в Dead Letter Queue."""
        ...
