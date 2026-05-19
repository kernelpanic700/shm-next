# =============================================================================
# shm-next — Payment Application Service
# =============================================================================
"""
Application Service для работы с платежами.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import structlog

from app.core.domain.entities.payment import Payment, PaymentStatus
from app.core.domain.repositories.abonent import AbonentRepositoryProtocol
from app.core.domain.repositories.payment import PaymentRepositoryProtocol
from app.core.services.event_bus import EventBus

logger = structlog.get_logger("payment_service")


class PaymentService:
    """
    Сервис работы с платежами.

    Use Cases:
    - Создание и обработка платежей
    - Подтверждение и возврат
    - Получение истории платежей
    """

    def __init__(
        self,
        payment_repo: PaymentRepositoryProtocol,
        abonent_repo: AbonentRepositoryProtocol,
        event_bus: EventBus,
    ) -> None:
        self._payment_repo = payment_repo
        self._abonent_repo = abonent_repo
        self._event_bus = event_bus

    async def create_payment(
        self,
        abonent_id: UUID,
        amount: float,
        currency: str = "RUB",
        payment_method: str = "cash",
        external_id: str | None = None,
    ) -> Payment:
        """
        Создать новый платёж.

        Args:
            abonent_id: ID абонента
            amount: Сумма платежа
            currency: Валюта
            payment_method: Способ оплаты
            external_id: Внешний ID из платёжной системы

        Returns:
            Payment: Созданный платёж

        Raises:
            ValueError: Если абонент не найден или сумма некорректна
        """
        # Проверяем существование абонента
        abonent = await self._abonent_repo.get(abonent_id)
        if abonent is None:
            raise ValueError(f"Abonent {abonent_id} not found")

        if amount <= 0:
            raise ValueError(f"Payment amount must be positive, got {amount}")

        from app.core.domain.entities.payment import Payment

        payment = Payment(
            abonent_id=abonent_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            external_id=external_id,
            status=PaymentStatus.NEW,
        )

        saved = await self._payment_repo.create(
            abonent_id=abonent_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            external_id=external_id,
        )

        # Публикуем событие
        from app.core.domain.events.billing_events import PaymentCompletedEvent

        event = PaymentCompletedEvent(
            abonent_id=str(abonent_id),
            payment_id=str(saved),
            amount=amount,
            currency=currency,
            payment_method=payment_method,
        )
        await self._event_bus.publish(event)

        logger.info(
            "Payment created",
            payment_id=saved,
            abonent_id=abonent_id,
            amount=amount,
        )

        # Возвращаем объект Payment
        payment._id = saved

        return payment

    async def get_payment(self, payment_id: UUID) -> dict | None:
        """Получить платёж по ID."""
        return await self._payment_repo.get(payment_id)

    async def get_payments_by_abonent(
        self,
        abonent_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 50,
    ) -> list:
        """Получить историю платежей абонента."""
        return await self._payment_repo.get_by_abonent(
            abonent_id=abonent_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
        )

    async def confirm_payment(self, payment_id: UUID) -> bool:
        """
        Подтвердить платёж.

        Используется при callback от платёжной системы.
        """
        result = await self._payment_repo.confirm(payment_id)

        if result:
            logger.info("Payment confirmed", payment_id=payment_id)
        else:
            logger.warning(
                "Payment confirmation failed",
                payment_id=payment_id,
            )

        return result

    async def refund_payment(self, payment_id: UUID) -> bool:
        """
        Выполнить возврат платежа.

        Args:
            payment_id: ID платежа для возврата

        Returns:
            bool: True если возврат выполнен успешно
        """
        result = await self._payment_repo.refund(payment_id)

        if result:
            logger.info("Payment refunded", payment_id=payment_id)
        else:
            logger.warning(
                "Payment refund failed",
                payment_id=payment_id,
            )

        return result
