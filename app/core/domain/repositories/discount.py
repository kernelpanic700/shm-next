# =============================================================================
# shm-next — Discount Repository Protocol
# =============================================================================
"""Протокол репозитория скидок."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.core.domain.entities.discount import Discount


class DiscountRepositoryProtocol(ABC):
    """Протокол репозитория скидок."""

    @abstractmethod
    async def get(self, discount_id: UUID) -> Discount | None:
        """Получить скидку по ID."""
        ...

    @abstractmethod
    async def get_active(self) -> list[Discount]:
        """Получить все активные скидки."""
        ...

    @abstractmethod
    async def get_valid_at(self, dt: datetime) -> list[Discount]:
        """Получить скидки, действующие в указанный момент."""
        ...

    @abstractmethod
    async def save(self, discount: Discount) -> Discount:
        """Сохранить скидку."""
        ...
