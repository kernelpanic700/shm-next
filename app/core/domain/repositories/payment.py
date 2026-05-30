# =============================================================================
# shm-next — Payment Repository Protocol
# =============================================================================
"""Протокол репозитория платежей."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class PaymentRepositoryProtocol(ABC):
    """Протокол репозитория платежей."""

    @abstractmethod
    async def create(
        self,
        abonent_id: UUID,
        amount: float,
        currency: str,
        payment_method: str,
        external_id: str | None = None,
    ) -> UUID:
        """Создать платёж."""
        ...

    @abstractmethod
    async def get(self, payment_id: UUID) -> dict | None:
        """Получить платёж по ID."""
        ...

    @abstractmethod
    async def get_by_abonent(
        self,
        abonent_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 50,
    ) -> list:
        """Получить платежи абонента."""
        ...

    @abstractmethod
    async def get_all(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 50,
    ) -> list:
        """Получить все платежи."""
        ...

    @abstractmethod
    async def confirm(self, payment_id: UUID) -> bool:
        """Подтвердить платёж."""
        ...

    @abstractmethod
    async def refund(self, payment_id: UUID) -> bool:
        """Выполнить возврат."""
        ...
