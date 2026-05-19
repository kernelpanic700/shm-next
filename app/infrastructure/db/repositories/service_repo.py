# =============================================================================
# shm-next — Service Repository
# =============================================================================
from __future__ import annotations

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

    async def save(self, service: UserService) -> UserService:
        """Сохранить услугу."""
        # Check if model exists
        existing = await self._session.get(ServiceModel, service.id)
        if existing:
            # Update existing
            existing.abonent_id = service.abonent_id
            existing.service_type = service.service_type
            existing.tariff_service_id = service.tariff_service_id
            existing.status = service.status.value
            existing.activated_at = service.activated_at
            existing.deactivated_at = service.deactivated_at
            existing.cost = service.cost
            existing.currency = service.currency
            existing.meta = service.meta
            existing.version = service.version
            model = existing
        else:
            # Create new
            model = ServiceModel(
                id=service.id,
                abonent_id=service.abonent_id,
                service_type=service.service_type,
                tariff_service_id=service.tariff_service_id,
                status=service.status.value,
                activated_at=service.activated_at,
                deactivated_at=service.deactivated_at,
                cost=service.cost,
                currency=service.currency,
                meta=service.meta,
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
            balance=Money(model.balance, "RUB") if isinstance(model.balance, (int, float)) else model.balance,
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
            status=ServiceStatus(model.status),
            activated_at=model.activated_at,
            deactivated_at=model.deactivated_at,
            cost=model.cost,
            currency=model.currency,
            metadata=model.meta,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )
