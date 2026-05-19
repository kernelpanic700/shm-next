# =============================================================================
# shm-next — Billing Process Service
# =============================================================================
"""
Сервис обработки биллинга.

Выполняет периодические списания за услуги абонентов.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from app.core.domain.repositories.abonent import AbonentRepositoryProtocol
from app.core.domain.repositories.service import ServiceRepositoryProtocol
from app.core.services.billing_engine import BillingEngine
from app.core.services.event_bus import EventBus
from app.infrastructure.external.action_registry import ActionRegistry


class ProcessBillingService:
    """
    Сервис обработки биллинга.

    Основные операции:
    - process_all_expired: Обработка всех абонентов с просроченными платежами
    - process_single: Обработка одного абонента
    """

    def __init__(
        self,
        abonent_repo: AbonentRepositoryProtocol,
        service_repo: ServiceRepositoryProtocol,
        billing_engine: BillingEngine,
        event_bus: EventBus,
        action_registry: ActionRegistry,
    ) -> None:
        self._abonent_repo = abonent_repo
        self._service_repo = service_repo
        self._billing_engine = billing_engine
        self._event_bus = event_bus
        self._action_registry = action_registry

    async def process_all_expired(
        self,
        batch_size: int = 100,
    ) -> dict[str, Any]:
        """
        Обработка всех абонентов с задолженностью.

        Args:
            batch_size: Размер пакета для обработки

        Returns:
            dict со статистикой
        """
        stats = {
            "total_processed": 0,
            "successful_withdraws": 0,
            "failed_withdraws": 0,
            "total_amount": 0.0,
            "currency": "RUB",
        }

        # Получаем абонентов с отрицательным балансом или просроченными услугами
        abonents = await self._abonent_repo.list(
            offset=0, limit=batch_size, status="ACTIVE"
        )

        for abonent in abonents:
            try:
                result = await self.process_single(abonent.id)
                stats["total_processed"] += 1
                if result.get("success"):
                    stats["successful_withdraws"] += 1
                    stats["total_amount"] += result.get("amount", 0)
                else:
                    stats["failed_withdraws"] += 1
            except Exception:
                stats["failed_withdraws"] += 1

        return stats

    async def process_single(self, abonent_id: UUID) -> dict[str, Any]:
        """
        Обработка биллинга для одного абонента.

        Args:
            abonent_id: ID абонента

        Returns:
            dict с результатами обработки
        """
        from app.core.domain.value_objects import Money

        # Получаем услуги абонента
        services = await self._service_repo.get_by_abonent(abonent_id, active_only=True)

        if not services:
            return {"success": True, "message": "No active services"}

        total_amount = 0.0
        currency = "RUB"

        for service in services:
            # Рассчитываем стоимость за период
            cost_per_day = Money(service.cost / 30, service.currency)
            period_start = service.activated_at.date() if service.activated_at else date.today()
            period_end = date.today()

            amount = self._billing_engine.calculate_withdraw(
                cost_per_day=cost_per_day,
                period_start=period_start,
                period_end=period_end,
                strategy="honest",
            )

            total_amount += float(amount.amount)
            currency = amount.currency.value

        return {
            "success": True,
            "amount": total_amount,
            "currency": currency,
            "services_count": len(services),
        }
