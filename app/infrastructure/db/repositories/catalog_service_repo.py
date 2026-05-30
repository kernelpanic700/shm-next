# =============================================================================
# shm-next - CatalogService Repository
# =============================================================================
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.entities.catalog_service import CatalogService
from app.core.domain.repositories.catalog_service import (
    CatalogServiceRepositoryProtocol,
)
from app.core.domain.value_objects import Money
from app.infrastructure.db.models import CatalogServiceModel


class CatalogServiceRepository(CatalogServiceRepositoryProtocol):
    """Репозиторий каталожных услуг SHM."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, service_id: UUID) -> CatalogService | None:
        model = await self._session.get(CatalogServiceModel, service_id)
        return self._to_domain(model) if model else None

    async def get_orderable(self) -> list[CatalogService]:
        stmt = (
            select(CatalogServiceModel)
            .where(CatalogServiceModel.allow_to_order.is_(True))
            .where(CatalogServiceModel.is_deleted.is_(False))
            .order_by(CatalogServiceModel.category, CatalogServiceModel.name)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]

    async def list(
        self,
        category: str | None = None,
        include_deleted: bool = False,
    ) -> list[CatalogService]:
        stmt = select(CatalogServiceModel).order_by(
            CatalogServiceModel.category,
            CatalogServiceModel.name,
        )
        if category:
            stmt = stmt.where(CatalogServiceModel.category == category)
        if not include_deleted:
            stmt = stmt.where(CatalogServiceModel.is_deleted.is_(False))

        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]

    async def save(self, service: CatalogService) -> CatalogService:
        model = await self._session.get(CatalogServiceModel, service.id)
        children = [str(child_id) for child_id in service.children]

        if model is None:
            model = CatalogServiceModel(id=service.id)
            self._session.add(model)

        model.legacy_service_id = service.legacy_service_id
        model.name = service.name
        model.cost = service.cost.amount
        model.currency = service.cost.currency.value
        model.period_cost = service.period_cost
        model.category = service.category
        model.children = children or None
        model.next_service_id = service.next_service_id
        model.allow_to_order = service.allow_to_order
        model.max_count = service.max_count
        model.question = service.question
        model.pay_always = service.pay_always
        model.no_discount = service.no_discount
        model.description = service.description
        model.pay_in_credit = service.pay_in_credit
        model.config = service.config or None
        model.is_composite = service.is_composite
        model.is_deleted = service.is_deleted
        model.version = service.version

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: CatalogServiceModel) -> CatalogService:
        children = [UUID(value) for value in (model.children or [])]
        return CatalogService(
            id=model.id,
            legacy_service_id=model.legacy_service_id,
            name=model.name,
            cost=Money(model.cost, model.currency),
            period_cost=model.period_cost,
            category=model.category,
            children=children,
            next_service_id=model.next_service_id,
            allow_to_order=model.allow_to_order,
            max_count=model.max_count,
            question=model.question,
            pay_always=model.pay_always,
            no_discount=model.no_discount,
            description=model.description,
            pay_in_credit=model.pay_in_credit,
            config=model.config,
            is_composite=model.is_composite,
            is_deleted=model.is_deleted,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )
