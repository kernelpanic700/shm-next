# =============================================================================
# shm-next — BonusEntry Repository Protocol
# =============================================================================
"""Протокол репозитория бонусных записей."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.entities.bonus_entry import BonusEntry


class BonusEntryRepositoryProtocol(ABC):
    """Протокол репозитория бонусных записей."""

    @abstractmethod
    async def get(self, entry_id: UUID) -> BonusEntry | None:
        """Получить бонусную запись по ID."""
        ...

    @abstractmethod
    async def get_by_abonent(self, abonent_id: UUID) -> list[BonusEntry]:
        """Получить бонусные записи абонента."""
        ...

    @abstractmethod
    async def get_active(self) -> list[BonusEntry]:
        """Получить все активные бонусные записи."""
        ...

    @abstractmethod
    async def get_expired(self) -> list[BonusEntry]:
        """Получить истёкшие бонусные записи."""
        ...

    @abstractmethod
    async def save(self, entry: BonusEntry) -> BonusEntry:
        """Сохранить бонусную запись."""
        ...
