# =============================================================================
# shm-next — Invoice Repository Protocol
# =============================================================================
"""Протокол репозитория счетов."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.core.domain.entities.invoice import Invoice


class InvoiceRepositoryProtocol(ABC):
    """Протокол репозитория счетов."""

    @abstractmethod
    async def get(self, invoice_id: UUID) -> Invoice | None:
        """Получить счёт по ID."""
        ...

    @abstractmethod
    async def get_by_abonent(
        self,
        abonent_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[Invoice]:
        """Получить счета абонента."""
        ...

    @abstractmethod
    async def list(
        self,
        status: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Invoice], int]:
        """Получить список счетов."""
        ...

    @abstractmethod
    async def get_unpaid(self) -> list[Invoice]:
        """Получить неоплаченные счета."""
        ...

    @abstractmethod
    async def get_overdue(self) -> list[Invoice]:
        """Получить просроченные счета."""
        ...

    @abstractmethod
    async def get_due_for_overdue(
        self,
        now: datetime,
        limit: int = 100,
    ) -> list[Invoice]:
        """Получить выставленные счета, у которых истёк срок оплаты."""
        ...

    @abstractmethod
    async def save(self, invoice: Invoice) -> Invoice:
        """Сохранить счёт."""
        ...
