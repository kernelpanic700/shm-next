# =============================================================================
# shm-next — Billing Repository
# =============================================================================
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.repositories.billing import BillingRepositoryProtocol
from app.infrastructure.db.models import AbonentModel, PaymentModel, ServiceModel, TariffModel, WithdrawModel


class BillingRepository(BillingRepositoryProtocol):
    """Репозиторий для биллинговых операций."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_abonent_balance(self, abonent_id: UUID) -> float:
        """Получить баланс абонента."""
        result = await self._session.get(AbonentModel, abonent_id)
        return result.balance if result else 0.0

    async def get_abonent_services(
        self, abonent_id: UUID, active_only: bool = True
    ) -> list:
        """Получить услуги абонента."""
        stmt = select(ServiceModel).where(
            ServiceModel.abonent_id == abonent_id
        )

        if active_only:
            stmt = stmt.where(ServiceModel.status == "ACTIVE")

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create_withdraw(
        self,
        abonent_id: UUID,
        service_id: UUID,
        amount: float,
        currency: str,
    ) -> UUID:
        """Создать запись о списании."""
        from uuid import uuid4

        withdraw = WithdrawModel(
            id=uuid4(),
            abonent_id=abonent_id,
            service_id=service_id,
            amount=amount,
            currency=currency,
            status="PENDING",
        )

        self._session.add(withdraw)
        await self._session.flush()
        return withdraw.id

    async def get_abonent_tariff(self, abonent_id: UUID) -> dict | None:
        """Получить тариф абонента."""
        stmt = (
            select(AbonentModel, TariffModel)
            .join(TariffModel, AbonentModel.tariff_id == TariffModel.id, isouter=True)
            .where(AbonentModel.id == abonent_id)
        )

        result = await self._session.execute(stmt)
        row = result.first()

        if row and row.TariffModel:
            return {
                "id": str(row.TariffModel.id),
                "name": row.TariffModel.name,
                "price": row.TariffModel.price,
                "currency": row.TariffModel.currency,
                "billing_period": row.TariffModel.billing_period,
                "services": row.TariffModel.services,
            }
        return None

    async def get_abonent_last_payment(self, abonent_id: UUID) -> dict | None:
        """Получить последний платёж абонента."""
        stmt = (
            select(PaymentModel)
            .where(PaymentModel.abonent_id == abonent_id)
            .order_by(PaymentModel.created_at.desc())
            .limit(1)
        )

        result = await self._session.execute(stmt)
        payment = result.scalar_one_or_none()

        if payment:
            return {
                "id": str(payment.id),
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "payment_method": payment.payment_method,
                "created_at": payment.created_at,
            }
        return None
