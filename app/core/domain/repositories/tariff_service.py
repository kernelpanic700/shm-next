# =============================================================================
# shm-next — TariffService Repository Protocol
# =============================================================================
"""Протокол репозитория услуг тарифа."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.entities.tariff_service import TariffService


class TariffServiceRepositoryProtocol(ABC):
    """Протокол репозитория услуг тарифа."""

    @abstractmethod
    async def get(self, tariff_service_id: UUID) -> TariffService | None:
        """Получить услугу тарифа по ID."""
        ...

    @abstractmethod
    async def get_by_tariff(self, tariff_id: UUID) -> list[TariffService]:
        """Получить все услуги указанного тарифа."""
        ...

    @abstractmethod
    async def get_by_service_type(
        self, service_type: str, tariff_id: UUID | None = None
    ) -> list[TariffService]:
        """Получить услуги по типу, опционально отфильтрованные по тарифу."""
        ...

    @abstractmethod
    async def save(self, tariff_service: TariffService) -> TariffService:
        """Сохранить услугу тарифа."""
        ...
