# =============================================================================
# shm-next — Tariff Repository
# =============================================================================
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.entities.tariff import Tariff
from app.core.domain.repositories.tariff import TariffRepositoryProtocol
from app.infrastructure.db.models import TariffModel, TariffServiceModel


class TariffRepository(TariffRepositoryProtocol):
    """Репозиторий тарифов."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, tariff_id: UUID) -> Tariff | None:
        """Получить тариф по ID."""
        model = await self._session.get(TariffModel, tariff_id)
        return self._to_domain(model) if model else None

    async def get_by_name(self, name: str) -> Tariff | None:
        """Получить тариф по имени."""
        stmt = select(TariffModel).where(TariffModel.name == name)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list(self, active_only: bool = True) -> list[Tariff]:
        """Список тарифов."""
        stmt = select(TariffModel)

        if active_only:
            stmt = stmt.where(TariffModel.is_active)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def save(self, tariff: Tariff) -> Tariff:
        """Сохранить тариф."""
        # Check if model exists
        existing = await self._session.get(TariffModel, tariff.id)
        if existing:
            # Update existing
            existing.name = tariff.name
            existing.description = tariff.description
            existing.services = tariff.services
            existing.is_active = tariff.is_active
            existing.price = tariff.price
            existing.currency = tariff.currency
            existing.billing_period = tariff.billing_period
            existing.version = tariff.version
            model = existing
        else:
            # Create new
            model = TariffModel(
                id=tariff.id,
                name=tariff.name,
                description=tariff.description,
                services=tariff.services,
                is_active=tariff.is_active,
                price=tariff.price,
                currency=tariff.currency,
                billing_period=tariff.billing_period,
                version=tariff.version,
            )
            self._session.add(model)

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_services_for_tariff(self, tariff_id: UUID) -> list[dict]:
        """Получить услуги тарифа."""
        stmt = select(TariffServiceModel).where(
            TariffServiceModel.tariff_id == tariff_id
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [
            {
                "id": m.id,
                "service_type": m.service_type,
                "name": m.name,
                "cost": m.cost,
                "currency": m.currency,
                "unit": m.unit,
                "is_optional": m.is_optional,
            }
            for m in models
        ]

    def _to_domain(self, model: TariffModel) -> Tariff:
        """Конвертация модели в доменную сущность."""
        return Tariff(
            id=model.id,
            name=model.name,
            description=model.description,
            services=model.services,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
            price=model.price,
            currency=model.currency,
            billing_period=model.billing_period,
        )
