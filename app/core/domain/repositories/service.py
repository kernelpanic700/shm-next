# =============================================================================
# shm-next — Service Repository Protocol
# =============================================================================
"""Протокол репозитория услуг."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.core.domain.entities.abonent import Abonent
from app.core.domain.entities.service import UserService


class ServiceRepositoryProtocol(ABC):
    """Протокол репозитория услуг абонентов."""

    @abstractmethod
    async def get_abonent(self, abonent_id: UUID) -> Abonent | None:
        """Получить абонента по ID (для проверки статуса)."""
        ...

    @abstractmethod
    async def save_abonent(self, abonent: Abonent) -> Abonent:
        """Сохранить абонента после изменения баланса/статуса."""
        ...

    @abstractmethod
    async def get(self, service_id: UUID) -> UserService | None:
        """Получить услугу по ID."""
        ...

    @abstractmethod
    async def get_by_abonent(
        self, abonent_id: UUID, active_only: bool = True
    ) -> list[UserService]:
        """Получить услуги абонента."""
        ...

    @abstractmethod
    async def get_active_by_abonent(
        self, abonent_id: UUID, service_type: str | None = None
    ) -> list[UserService]:
        """Получить активные услуги абонента по типу."""
        ...

    @abstractmethod
    async def get_expiring_auto_bill(
        self,
        cutoff: datetime,
        limit: int = 100,
    ) -> list[UserService]:
        """Получить SHM-услуги для автоматического продления."""
        ...

    @abstractmethod
    async def save(self, service: UserService) -> UserService:
        """Сохранить услугу."""
        ...
