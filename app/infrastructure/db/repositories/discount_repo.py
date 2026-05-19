# =============================================================================
# shm-next — Discount Repository
# =============================================================================
"""Репозиторий скидок."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.entities.discount import Discount
from app.core.domain.repositories.discount import DiscountRepositoryProtocol
from app.infrastructure.db.models import DiscountModel


class DiscountRepository(DiscountRepositoryProtocol):
    """Репозиторий скидок."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, discount_id: UUID) -> Discount | None:
        """Получить скидку по ID."""
        model = await self._session.get(DiscountModel, discount_id)
        return self._to_domain(model) if model else None

    async def get_active(self) -> list[Discount]:
        """Получить все активные скидки."""
        stmt = select(DiscountModel).where(DiscountModel.is_active)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_valid_at(self, dt: datetime) -> list[Discount]:
        """Получить скидки, действующие в указанный момент."""
        from datetime import UTC
        
        stmt = select(DiscountModel).where(DiscountModel.is_active)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        discounts = []
        for m in models:
            # Ensure both datetimes are timezone-aware for comparison
            check_dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt
            valid_from = m.valid_from
            if valid_from and valid_from.tzinfo is None:
                valid_from = valid_from.replace(tzinfo=UTC)
            valid_to = m.valid_to
            if valid_to and valid_to.tzinfo is None:
                valid_to = valid_to.replace(tzinfo=UTC)
            
            if valid_from and check_dt < valid_from:
                continue
            if valid_to and check_dt > valid_to:
                continue
            if m.max_uses is not None and m.used_count >= m.max_uses:
                continue
            discounts.append(self._to_domain(m))
        return discounts

    async def save(self, discount: Discount) -> Discount:
        """Сохранить скидку."""
        # Check if model exists
        existing = await self._session.get(DiscountModel, discount.id)
        if existing:
            # Update existing
            existing.name = discount.name
            existing.description = discount.description
            existing.discount_type = discount.discount_type
            existing.value = discount.value
            existing.currency = discount.currency
            existing.valid_from = discount.valid_from
            existing.valid_to = discount.valid_to
            existing.is_active = discount.is_active
            existing.max_uses = discount.max_uses
            existing.used_count = discount.used_count
            existing.version = discount.version
            model = existing
        else:
            # Create new
            model = DiscountModel(
                id=discount.id,
                name=discount.name,
                description=discount.description,
                discount_type=discount.discount_type,
                value=discount.value,
                currency=discount.currency,
                valid_from=discount.valid_from,
                valid_to=discount.valid_to,
                is_active=discount.is_active,
                max_uses=discount.max_uses,
                used_count=discount.used_count,
                version=discount.version,
            )
            self._session.add(model)

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: DiscountModel) -> Discount:
        """Конвертация модели в доменную сущность."""
        return Discount(
            id=model.id,
            name=model.name,
            description=model.description,
            discount_type=model.discount_type,
            value=model.value,
            currency=model.currency,
            valid_from=model.valid_from,
            valid_to=model.valid_to,
            is_active=model.is_active,
            max_uses=model.max_uses,
            used_count=model.used_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )
