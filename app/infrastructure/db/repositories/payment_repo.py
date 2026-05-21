# =============================================================================
# shm-next — Payment Repository
# =============================================================================
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.repositories.payment import PaymentRepositoryProtocol
from app.infrastructure.db.models import PaymentModel


class PaymentRepository(PaymentRepositoryProtocol):
    """Репозиторий платежей."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        abonent_id: UUID,
        amount: float,
        currency: str,
        payment_method: str,
        external_id: str | None = None,
    ) -> UUID:
        """Создать платёж."""
        payment = PaymentModel(
            abonent_id=abonent_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            external_id=external_id,
            status="NEW",
        )

        self._session.add(payment)
        await self._session.flush()
        return payment.id

    async def get(self, payment_id: UUID) -> dict | None:
        """Получить платёж по ID."""
        payment = await self._session.get(PaymentModel, payment_id)

        if payment:
            return {
                "id": str(payment.id),
                "abonent_id": str(payment.abonent_id),
                "amount": payment.amount,
                "currency": payment.currency,
                "payment_method": payment.payment_method,
                "status": payment.status,
                "external_id": payment.external_id,
                "created_at": payment.created_at,
                "completed_at": payment.completed_at,
            }
        return None

    async def get_by_abonent(
        self,
        abonent_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 50,
    ) -> list:
        """Получить платежи абонента."""
        stmt = select(PaymentModel).where(
            PaymentModel.abonent_id == abonent_id
        )

        if from_date:
            stmt = stmt.where(PaymentModel.created_at >= from_date)
        if to_date:
            stmt = stmt.where(PaymentModel.created_at <= to_date)

        stmt = stmt.order_by(PaymentModel.created_at.desc()).limit(limit)

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def confirm(self, payment_id: UUID) -> bool:
        """Подтвердить платёж."""
        payment = await self._session.get(PaymentModel, payment_id)

        if payment and payment.status == "NEW":
            payment.status = "COMPLETED"
            payment.completed_at = datetime.now(UTC)
            await self._session.flush()
            return True
        return False

    async def refund(self, payment_id: UUID) -> bool:
        """Выполнить возврат."""
        payment = await self._session.get(PaymentModel, payment_id)

        if payment and payment.status == "COMPLETED":
            payment.status = "REFUNDED"
            await self._session.flush()
            return True
        return False
