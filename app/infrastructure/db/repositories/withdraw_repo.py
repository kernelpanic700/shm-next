# =============================================================================
# shm-next — Withdraw Repository
# =============================================================================
"""Репозиторий списаний."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.entities.withdraw import Withdraw
from app.core.domain.repositories.withdraw import WithdrawRepositoryProtocol
from app.infrastructure.db.models import WithdrawModel


class WithdrawRepository(WithdrawRepositoryProtocol):
    """Репозиторий списаний."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, withdraw_id: UUID) -> Withdraw | None:
        """Получить списание по ID."""
        model = await self._session.get(WithdrawModel, str(withdraw_id))
        return self._to_domain(model) if model else None

    async def get_by_abonent(
        self,
        abonent_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 50,
    ) -> list[Withdraw]:
        """Получить списания абонента."""
        stmt = select(WithdrawModel).where(
            WithdrawModel.abonent_id == str(abonent_id)
        )

        if from_date:
            stmt = stmt.where(WithdrawModel.created_at >= from_date)
        if to_date:
            stmt = stmt.where(WithdrawModel.created_at <= to_date)

        stmt = stmt.order_by(WithdrawModel.created_at.desc()).limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_pending(self, limit: int = 100) -> list[Withdraw]:
        """Получить списания в статусе NEW/PENDING."""
        stmt = select(WithdrawModel).where(
            WithdrawModel.status.in_(["NEW", "PENDING"])
        )
        stmt = stmt.order_by(WithdrawModel.created_at.asc()).limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_by_service(self, service_id: UUID) -> list[Withdraw]:
        """Получить списания по услуге."""
        stmt = select(WithdrawModel).where(
            WithdrawModel.service_id == str(service_id)
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def save(self, withdraw: Withdraw) -> Withdraw:
        """Сохранить списание."""
        # Convert UUID to string for SQLite compatibility
        withdraw_id = str(withdraw.id)
        abonent_id = str(withdraw.abonent_id) if withdraw.abonent_id else None
        service_id = str(withdraw.service_id) if withdraw.service_id else None

        # Check if model exists for upsert
        existing = await self._session.get(WithdrawModel, withdraw_id)
        status_value = withdraw.status.value if hasattr(withdraw.status, 'value') else withdraw.status
        if existing:
            existing.abonent_id = abonent_id
            existing.service_id = service_id
            existing.amount = withdraw.amount
            existing.currency = withdraw.currency
            existing.status = status_value
            existing.strategy = withdraw.strategy
            existing.completed_at = withdraw.completed_at
            existing.error_message = withdraw.error_message
            existing.meta = withdraw.meta
            existing.version = withdraw.version
            existing.created_at = withdraw.created_at
            existing.updated_at = withdraw.updated_at
            model = existing
        else:
            model = WithdrawModel(
                id=withdraw_id,
                abonent_id=abonent_id,
                service_id=service_id,
                amount=withdraw.amount,
                currency=withdraw.currency,
                status=status_value,
                strategy=withdraw.strategy,
                completed_at=withdraw.completed_at,
                error_message=withdraw.error_message,
                meta=withdraw.meta,
                version=withdraw.version,
                created_at=withdraw.created_at,
                updated_at=withdraw.updated_at,
            )
            self._session.add(model)

        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: WithdrawModel) -> Withdraw:
        """Конвертация модели в доменную сущность."""
        from app.core.domain.value_objects import WithdrawStatus

        return Withdraw(
            id=UUID(model.id) if model.id else None,
            abonent_id=UUID(model.abonent_id) if model.abonent_id else None,
            service_id=UUID(model.service_id) if model.service_id else None,
            amount=model.amount,
            currency=model.currency,
            status=WithdrawStatus(model.status),
            strategy=model.strategy,
            completed_at=model.completed_at,
            error_message=model.error_message,
            metadata=model.meta,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )
