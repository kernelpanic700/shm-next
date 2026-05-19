# =============================================================================
# shm-next — Base Repository Protocol
# =============================================================================
"""
Базовый протокол репозитория.

Определяет общий контракт для всех репозиториев доменного слоя.
Все специализированные репозитории наследуют этот интерфейс.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Generic, TypeVar
from uuid import UUID

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Базовый абстрактный репозиторий.

    Определяет стандартный набор CRUD-операций для всех агрегатов.
    Конкретные реализации могут добавлять специфичные методы.
    """

    @abstractmethod
    async def get(self, entity_id: UUID) -> T | None:
        """Получить сущность по ID."""
        ...

    @abstractmethod
    async def get_all(self, offset: int = 0, limit: int = 50) -> Sequence[T]:
        """Получить все сущности с пагинацией."""
        ...

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Сохранить сущность (create или update)."""
        ...

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Удалить сущность по ID."""
        ...

    @abstractmethod
    async def exists(self, entity_id: UUID) -> bool:
        """Проверить существование сущности."""
        ...

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Подсчёт сущностей с опциональными фильтрами."""
        ...
