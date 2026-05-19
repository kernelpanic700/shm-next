# =============================================================================
# shm-next — Tariff Repository Protocol
# =============================================================================
"""Протокол репозитория тарифов."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.entities.tariff import Tariff


class TariffRepositoryProtocol(ABC):
    """Протокол репозитория тарифов."""

    @abstractmethod
    async def get(self, tariff_id: UUID) -> Tariff | None:
        """Получить тариф по ID."""
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Tariff | None:
        """Получить тариф по имени."""
        ...

    @abstractmethod
    async def list(self, active_only: bool = True) -> list[Tariff]:
        """Список тарифов."""
        ...

    @abstractmethod
    async def save(self, tariff: Tariff) -> Tariff:
        """Сохранить тариф."""
        ...

    @abstractmethod
    async def get_services_for_tariff(self, tariff_id: UUID) -> list[dict]:
        """Получить услуги тарифа."""
        ...
