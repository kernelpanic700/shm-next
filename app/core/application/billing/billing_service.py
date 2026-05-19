# =============================================================================
# shm-next — Billing Application Service
# =============================================================================
"""
Application Service для биллинга.

Координирует расчёт списаний и управление балансами.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

import structlog

from app.core.domain.repositories.abonent import AbonentRepositoryProtocol
from app.core.domain.repositories.billing import BillingRepositoryProtocol
from app.core.domain.repositories.service import ServiceRepositoryProtocol
from app.core.domain.repositories.withdraw import WithdrawRepositoryProtocol
from app.core.domain.value_objects import Money
from app.core.services.billing_engine import BillingEngine
from app.core.services.event_bus import EventBus

logger = structlog.get_logger("billing_service")


class BillingService:
    """
    Сервис биллинга.

    Use Cases:
    - Расчёт списаний за период
    - Получение баланса
    - История списаний
    """

    def __init__(
        self,
        abonent_repo: AbonentRepositoryProtocol,
        billing_repo: BillingRepositoryProtocol,
        service_repo: ServiceRepositoryProtocol,
        withdraw_repo: WithdrawRepositoryProtocol,
        event_bus: EventBus,
        billing_engine: BillingEngine | None = None,
    ) -> None:
        self._abonent_repo = abonent_repo
        self._billing_repo = billing_repo
        self._service_repo = service_repo
        self._withdraw_repo = withdraw_repo
        self._event_bus = event_bus
        self._billing_engine = billing_engine or BillingEngine(strategy="honest")

    async def get_balance(self, abonent_id: UUID) -> dict:
        """
        Получить баланс абонента.

        Returns:
            dict: {balance, currency, available}
        """
        abonent = await self._abonent_repo.get(abonent_id)

        if abonent is None:
            raise ValueError(f"Abonent {abonent_id} not found")

        return {
            "balance": float(abonent.balance.amount),
            "currency": abonent.balance.currency.value
            if hasattr(abonent.balance, "currency")
            else "RUB",
            "available": abonent.balance.amount >= 0 or abonent.allow_negative,
            "allow_negative": abonent.allow_negative,
        }

    async def calculate_withdraw(
        self,
        abonent_id: UUID,
        service_id: UUID,
        period_start: date,
        period_end: date,
    ) -> Money:
        """
        Рассчитать сумму списания за период.
        """
        services = await self._billing_repo.get_abonent_services(
            abonent_id, active_only=True
        )

        service = None
        for s in services:
            if s.id == service_id:
                service = s
                break

        if service is None:
            raise ValueError(f"Service {service_id} not found or not active")

        cost_per_day = Money(service.cost / 30, service.currency)

        return self._billing_engine.calculate_withdraw(
            cost_per_day=cost_per_day,
            period_start=period_start,
            period_end=period_end,
        )

    async def run_billing_for_abonent(
        self,
        abonent_id: UUID,
        period_start: date,
        period_end: date,
    ) -> list[dict]:
        """
        Выполнить биллинг для абонента за период.

        Returns:
            list: Список созданных списаний
        """
        services = await self._billing_repo.get_abonent_services(
            abonent_id, active_only=True
        )

        # Сначала рассчитываем все суммы
        calculated_withdraws = []
        for service in services:
            cost_per_day = Money(service.cost / 30, service.currency)

            amount = self._billing_engine.calculate_withdraw(
                cost_per_day=cost_per_day,
                period_start=period_start,
                period_end=period_end,
            )

            if float(amount.amount) > 0:
                calculated_withdraws.append({
                    "service_id": service.id,
                    "amount": float(amount.amount),
                    "currency": amount.currency.value
                    if hasattr(amount.currency, "value")
                    else "RUB",
                })

        if not calculated_withdraws:
            return []

        # Проверяем достаточность баланса перед созданием списаний
        total_amount = sum(w["amount"] for w in calculated_withdraws)
        abonent = await self._abonent_repo.get(abonent_id)

        if abonent:
            try:
                abonent.change_balance(
                    Money(-total_amount, "RUB"),
                    reason="Billing cycle",
                )
            except ValueError:
                logger.warning(
                    "Insufficient balance",
                    abonent_id=abonent_id,
                    amount=total_amount,
                )
                return []

            # Баланс достаточен — создаём списания
            withdraws = []
            for w in calculated_withdraws:
                withdraw_id = await self._withdraw_repo.create_withdraw(
                    abonent_id=abonent_id,
                    service_id=w["service_id"],
                    amount=w["amount"],
                    currency=w["currency"],
                )
                w["withdraw_id"] = withdraw_id
                withdraws.append(w)

            await self._abonent_repo.save(abonent)
            return withdraws

        return []
    async def get_withdraw_history(
        self,
        abonent_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 50,
    ) -> list:
        """Получить историю списаний."""
        return await self._withdraw_repo.get_by_abonent(
            abonent_id=abonent_id,
            limit=limit,
        )

    async def get_abonent_tariff_info(self, abonent_id: UUID) -> dict | None:
        """Получить информацию о тарифе абонента."""
        return await self._billing_repo.get_abonent_tariff(abonent_id)

    async def get_abonent_last_payment(self, abonent_id: UUID) -> dict | None:
        """Получить последний платёж абонента."""
        return await self._billing_repo.get_abonent_last_payment(abonent_id)
