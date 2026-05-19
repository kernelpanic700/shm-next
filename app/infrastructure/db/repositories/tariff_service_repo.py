# =============================================================================
# shm-next — TariffService Repository
# =============================================================================
"""Репозиторий услуг тарифа."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.entities.tariff_service import TariffService
from app.core.domain.repositories.tariff_service import TariffServiceRepositoryProtocol
from app.infrastructure.db.models import TariffServiceModel


class TariffServiceRepository(TariffServiceRepositoryProtocol):
    """Репозиторий услуг тарифа."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, tariff_service_id: UUID) -> TariffService | None:
        """Получить услугу тарифа по ID."""
        model = await self._session.get(TariffServiceModel, tariff_service_id)
        return self._to_domain(model) if model else None

    async def get_by_tariff(self, tariff_id: UUID) -> list[TariffService]:
        """Получить все услуги указанного тарифа."""
        stmt = select(TariffServiceModel).where(
            TariffServiceModel.tariff_id == tariff_id
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_by_service_type(
        self, service_type: str, tariff_id: UUID | None = None
    ) -> list[TariffService]:
        """Получить услуги по типу, опционально отфильтрованные по тарифу."""
        stmt = select(TariffServiceModel).where(
            TariffServiceModel.service_type == service_type
        )

        if tariff_id:
            stmt = stmt.where(TariffServiceModel.tariff_id == tariff_id)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def save(self, tariff_service: TariffService) -> TariffService:
        """Сохранить услугу тарифа."""
        # Check if model exists
        existing = await self._session.get(TariffServiceModel, tariff_service.id)
        if existing:
            # Update existing
            existing.tariff_id = tariff_service.tariff_id
            existing.service_type = tariff_service.service_type
            existing.name = tariff_service.name if hasattr(tariff_service, 'name') else tariff_service.service_type
            existing.cost = tariff_service.cost.amount if tariff_service.cost else 0
            existing.currency = tariff_service.currency if isinstance(tariff_service.currency, str) else "RUB"
            existing.is_optional = tariff_service.is_optional
            existing.sort_order = tariff_service.sort_order
            existing.version = tariff_service.version
            model = existing
        else:
            # Create new
            model = TariffServiceModel(
                id=tariff_service.id,
                tariff_id=tariff_service.tariff_id,
                service_type=tariff_service.service_type,
                name=tariff_service.name if hasattr(tariff_service, 'name') else tariff_service.service_type,
                cost=tariff_service.cost.amount if tariff_service.cost else 0,
                currency=tariff_service.currency if isinstance(tariff_service.currency, str) else "RUB",
                unit="day",
                is_optional=tariff_service.is_optional,
                sort_order=tariff_service.sort_order,
                version=tariff_service.version,
            )
            self._session.add(model)

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: TariffServiceModel) -> TariffService:
        """Конвертация модели в доменную сущность."""
        from app.core.domain.value_objects import Money

        return TariffService(
            id=model.id,
            tariff_id=model.tariff_id,
            service_type=model.service_type,
            name=model.name,
            cost=Money(model.cost, model.currency),
            billing_period="monthly",
            is_optional=model.is_optional,
            sort_order=model.sort_order,
            currency=model.currency,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )
