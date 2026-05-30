# =============================================================================
# shm-next — Service Repository
# =============================================================================
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.entities.abonent import Abonent
from app.core.domain.entities.service import UserService
from app.core.domain.repositories.service import ServiceRepositoryProtocol
from app.infrastructure.db.models import ServiceModel


class ServiceRepository(ServiceRepositoryProtocol):
    """Репозиторий услуг абонентов."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_abonent(self, abonent_id: UUID) -> Abonent | None:
        """Получить абонента по ID."""
        from app.infrastructure.db.models import AbonentModel
        model = await self._session.get(AbonentModel, abonent_id)
        return self._abonent_to_domain(model) if model else None

    async def save_abonent(self, abonent: Abonent) -> Abonent:
        """Сохранить абонента после изменения баланса/статуса."""
        from app.infrastructure.db.models import AbonentModel

        model = await self._session.get(AbonentModel, abonent.id)
        if model is None:
            raise ValueError(f"Abonent {abonent.id} not found")

        model.full_name = abonent.full_name
        model.phone = abonent.phone
        model.account_number = abonent.account_number
        model.email = abonent.email
        model.balance = abonent.balance.amount
        model.currency = abonent.balance.currency.value
        model.status = abonent.status.value
        model.allow_negative = abonent.allow_negative
        model.tariff_id = abonent.tariff_id
        model.password_hash = abonent.password_hash
        model.version = abonent.version

        await self._session.flush()
        await self._session.refresh(model)
        return self._abonent_to_domain(model)

    async def get(self, service_id: UUID) -> UserService | None:
        """Получить услугу по ID."""
        model = await self._session.get(ServiceModel, service_id)
        return self._to_domain(model) if model else None

    async def get_by_abonent(
        self, abonent_id: UUID, active_only: bool = True
    ) -> list[UserService]:
        """Получить услуги абонента."""
        stmt = select(ServiceModel).where(
            ServiceModel.abonent_id == abonent_id
        )

        if active_only:
            stmt = stmt.where(ServiceModel.status == "ACTIVE")

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_active_by_abonent(
        self, abonent_id: UUID, service_type: str | None = None
    ) -> list[UserService]:
        """Получить активные услуги абонента по типу."""
        stmt = select(ServiceModel).where(
            ServiceModel.abonent_id == abonent_id,
            ServiceModel.status == "ACTIVE",
        )

        if service_type:
            stmt = stmt.where(ServiceModel.service_type == service_type)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_expiring_auto_bill(
        self,
        cutoff: datetime,
        limit: int = 100,
    ) -> list[UserService]:
        """Получить активные родительские SHM-услуги для автопродления."""
        stmt = (
            select(ServiceModel)
            .where(
                ServiceModel.status == "ACTIVE",
                ServiceModel.auto_bill.is_(True),
                ServiceModel.catalog_service_id.is_not(None),
                ServiceModel.expire_at.is_not(None),
                ServiceModel.expire_at <= cutoff,
                ServiceModel.parent_id.is_(None),
            )
            .order_by(ServiceModel.expire_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def save(self, service: UserService) -> UserService:
        """Сохранить услугу."""
        # Check if model exists
        existing = await self._session.get(ServiceModel, service.id)
        if existing:
            # Update existing
            existing.abonent_id = service.abonent_id
            existing.service_type = service.service_type
            existing.tariff_service_id = service.tariff_service_id
            existing.catalog_service_id = service.catalog_service_id
            existing.status = service.status.value
            existing.activated_at = service.activated_at
            existing.deactivated_at = service.deactivated_at
            existing.expire_at = service.expire_at
            existing.cost = service.cost
            existing.currency = service.currency
            existing.meta = service.meta
            existing.period_cost = service.period_cost
            existing.next_service_id = service.next_service_id
            existing.parent_id = service.parent_id
            existing.quantity = service.quantity
            existing.auto_bill = service.auto_bill
            existing.pay_always = service.pay_always
            existing.pay_in_credit = service.pay_in_credit
            existing.no_discount = service.no_discount
            existing.version = service.version
            model = existing
        else:
            # Create new
            model = ServiceModel(
                id=service.id,
                abonent_id=service.abonent_id,
                service_type=service.service_type,
                tariff_service_id=service.tariff_service_id,
                catalog_service_id=service.catalog_service_id,
                status=service.status.value,
                activated_at=service.activated_at,
                deactivated_at=service.deactivated_at,
                expire_at=service.expire_at,
                cost=service.cost,
                currency=service.currency,
                meta=service.meta,
                period_cost=service.period_cost,
                next_service_id=service.next_service_id,
                parent_id=service.parent_id,
                quantity=service.quantity,
                auto_bill=service.auto_bill,
                pay_always=service.pay_always,
                pay_in_credit=service.pay_in_credit,
                no_discount=service.no_discount,
                version=service.version,
            )
            self._session.add(model)

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    def _abonent_to_domain(self, model) -> Abonent:
        """Конвертация модели абонента в доменную сущность."""
        from app.core.domain.value_objects import AbonentStatus, Money
        return Abonent(
            id=model.id,
            full_name=model.full_name,
            phone=model.phone,
            account_number=model.account_number,
            balance=Money(model.balance, "RUB")
            if isinstance(model.balance, (int, float, Decimal))
            else model.balance,
            status=AbonentStatus(model.status) if isinstance(model.status, str) else model.status,
            allow_negative=model.allow_negative if hasattr(model, 'allow_negative') else False,
        )

    def _to_domain(self, model: ServiceModel) -> UserService:
        """Конвертация модели в доменную сущность."""
        from app.core.domain.value_objects import ServiceStatus

        return UserService(
            id=model.id,
            abonent_id=model.abonent_id,
            service_type=model.service_type,
            tariff_service_id=model.tariff_service_id,
            catalog_service_id=model.catalog_service_id,
            status=ServiceStatus(model.status),
            activated_at=model.activated_at,
            deactivated_at=model.deactivated_at,
            expire_at=model.expire_at,
            cost=model.cost,
            currency=model.currency,
            period_cost=model.period_cost,
            next_service_id=model.next_service_id,
            parent_id=model.parent_id,
            quantity=model.quantity,
            auto_bill=model.auto_bill,
            pay_always=model.pay_always,
            pay_in_credit=model.pay_in_credit,
            no_discount=model.no_discount,
            metadata=model.meta,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )
