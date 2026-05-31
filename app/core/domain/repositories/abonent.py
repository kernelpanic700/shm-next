# =============================================================================
# shm-next — Abonent Repository Protocol
# =============================================================================
"""
Протокол репозитория абонентов.

Определяет контракт, которому должны соответствовать все реализации
(ORM, in-memory, тестовые моки и т.д.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.entities.abonent import Abonent


class AbonentRepositoryProtocol(ABC):
    """Протокол репозитория абонентов."""

    @abstractmethod
    async def get(self, abonent_id: UUID) -> Abonent | None:
        """Получить абонента по ID."""
        ...

    @abstractmethod
    async def get_by_phone(self, phone: str) -> Abonent | None:
        """Получить абонента по телефону."""
        ...

    @abstractmethod
    async def get_by_account(self, account_number: str) -> Abonent | None:
        """Получить абонента по номеру лицевого счёта."""
        ...

    @abstractmethod
    async def list(
        self,
        offset: int = 0,
        limit: int = 50,
        status: str | None = None,
    ) -> list[Abonent]:
        """Список абонентов с пагинацией."""
        ...

    @abstractmethod
    async def list_active(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Abonent]:
        """Список активных абонентов для биллинг-цикла."""
        ...

    @abstractmethod
    async def save(self, abonent: Abonent) -> Abonent:
        """Сохранить абонента (create или update)."""
        ...

    @abstractmethod
    async def delete(self, abonent_id: UUID) -> bool:
        """Удалить абонента."""
        ...

    @abstractmethod
    async def delete_inactive(self, abonent_id: UUID) -> bool:
        """Физически удалить неактивного абонента без финансовой истории."""
        ...

    @abstractmethod
    async def exists(self, abonent_id: UUID) -> bool:
        """Проверка существования абонента."""
        ...
