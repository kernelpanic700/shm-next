# =============================================================================
# shm-next — Billing Repository Protocol
# =============================================================================
"""Протокол репозитория для биллинговых операций."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class BillingRepositoryProtocol(ABC):
    """Протокол репозитория для биллинга."""

    @abstractmethod
    async def get_abonent_balance(self, abonent_id: UUID) -> float:
        """Получить баланс абонента."""
        ...

    @abstractmethod
    async def get_abonent_services(
        self, abonent_id: UUID, active_only: bool = True
    ) -> list:
        """Получить услуги абонента."""
        ...

    @abstractmethod
    async def create_withdraw(
        self,
        abonent_id: UUID,
        service_id: UUID,
        amount: float,
        currency: str,
    ) -> UUID:
        """Создать запись о списании."""
        ...

    @abstractmethod
    async def get_abonent_tariff(self, abonent_id: UUID) -> dict | None:
        """Получить тариф абонента."""
        ...

    @abstractmethod
    async def get_abonent_last_payment(self, abonent_id: UUID) -> dict | None:
        """Получить последний платёж абонента."""
        ...
