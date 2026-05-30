# =============================================================================
# shm-next — Withdraw Repository Protocol
# =============================================================================
"""Протокол репозитория списаний."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.core.domain.entities.withdraw import Withdraw


class WithdrawRepositoryProtocol(ABC):
    """Протокол репозитория списаний."""

    @abstractmethod
    async def get(self, withdraw_id: UUID) -> Withdraw | None:
        """Получить списание по ID."""
        ...

    @abstractmethod
    async def get_by_abonent(
        self,
        abonent_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 50,
    ) -> list[Withdraw]:
        """Получить списания абонента."""
        ...

    @abstractmethod
    async def get_pending(self, limit: int = 100) -> list[Withdraw]:
        """Получить списания в статусе NEW/PENDING."""
        ...

    @abstractmethod
    async def get_by_service(self, service_id: UUID) -> list[Withdraw]:
        """Получить списания по услуге."""
        ...

    @abstractmethod
    async def create_withdraw(
        self,
        abonent_id: UUID,
        service_id: UUID,
        amount: float,
        currency: str,
    ) -> UUID:
        """Создать списание и вернуть его ID."""
        ...

    @abstractmethod
    async def save(self, withdraw: Withdraw) -> Withdraw:
        """Сохранить списание."""
        ...
