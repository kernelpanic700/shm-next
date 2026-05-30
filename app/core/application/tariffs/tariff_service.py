# =============================================================================
# shm-next — Tariff Application Service
# =============================================================================
"""
Application Service для работы с тарифами.
"""

from __future__ import annotations

from uuid import UUID

import structlog

from app.core.domain.entities.tariff import Tariff
from app.core.domain.repositories.tariff import TariffRepositoryProtocol
from app.core.services.event_bus import EventBus

logger = structlog.get_logger("tariff_service")


class TariffService:
    """
    Сервис управления тарифами.
    """

    def __init__(
        self,
        tariff_repo: TariffRepositoryProtocol,
        event_bus: EventBus,
    ) -> None:
        self._tariff_repo = tariff_repo
        self._event_bus = event_bus

    async def get_tariff(self, tariff_id: UUID) -> Tariff | None:
        """Получить тариф по ID."""
        return await self._tariff_repo.get(tariff_id)

    async def get_tariff_by_name(self, name: str) -> Tariff | None:
        """Получить тариф по имени."""
        return await self._tariff_repo.get_by_name(name)

    async def list_tariffs(self, active_only: bool = True) -> list[Tariff]:
        """Список тарифов."""
        return await self._tariff_repo.list(active_only=active_only)

    async def get_tariff_services(self, tariff_id: UUID) -> list[dict]:
        """Получить услуги тарифа."""
        return await self._tariff_repo.get_services_for_tariff(tariff_id)

    async def create_tariff(self, data) -> Tariff:
        """Создать тариф из DTO."""
        tariff = Tariff(
            name=data.name,
            description=data.description or "",
            services=data.services,
            is_active=data.is_active,
            price=data.price,
            currency=data.currency,
            billing_period=data.billing_period,
        )
        saved = await self._tariff_repo.save(tariff)

        logger.info("Tariff created", tariff_id=saved.id, name=saved.name)
        return saved

    async def update_tariff(self, tariff_id: UUID, data) -> Tariff:
        """Обновить тариф из DTO."""

        tariff = await self._tariff_repo.get(tariff_id)
        if not tariff:
            raise ValueError(f"Tariff {tariff_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data:
            tariff._name = update_data["name"]
        if "description" in update_data:
            tariff._description = update_data["description"]
        if "services" in update_data:
            tariff._services = update_data["services"]
        if "is_active" in update_data:
            tariff._is_active = update_data["is_active"]
        if "price" in update_data:
            tariff._price = update_data["price"]
        if "currency" in update_data:
            tariff._currency = update_data["currency"]
        if "billing_period" in update_data:
            tariff._billing_period = update_data["billing_period"]

        saved = await self._tariff_repo.save(tariff)
        logger.info("Tariff updated", tariff_id=saved.id, name=saved.name)
        return saved

    async def deactivate_tariff(self, tariff_id: UUID) -> None:
        """Деактивировать тариф."""
        tariff = await self._tariff_repo.get(tariff_id)
        if not tariff:
            raise ValueError(f"Tariff {tariff_id} not found")
        tariff._is_active = False
        await self._tariff_repo.save(tariff)
        logger.info("Tariff deactivated", tariff_id=tariff_id)
