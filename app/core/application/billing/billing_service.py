# =============================================================================
# shm-next — Billing Application Service
# =============================================================================
"""
Application Service для биллинга.

Координирует расчёт списаний и управление балансами.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog

from app.core.domain.entities.invoice import Invoice
from app.core.domain.repositories.abonent import AbonentRepositoryProtocol
from app.core.domain.repositories.billing import BillingRepositoryProtocol
from app.core.domain.repositories.bonus_entry import BonusEntryRepositoryProtocol
from app.core.domain.repositories.invoice import InvoiceRepositoryProtocol
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
        invoice_repo: InvoiceRepositoryProtocol | None = None,
        bonus_entry_repo: BonusEntryRepositoryProtocol | None = None,
    ) -> None:
        self._abonent_repo = abonent_repo
        self._billing_repo = billing_repo
        self._service_repo = service_repo
        self._withdraw_repo = withdraw_repo
        self._event_bus = event_bus
        self._billing_engine = billing_engine or BillingEngine(strategy="honest")
        self._invoice_repo = invoice_repo
        self._bonus_entry_repo = bonus_entry_repo

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

        bonus_entries = []
        available_bonus = Money.zero("RUB")
        if self._bonus_entry_repo is not None:
            bonus_entries = await self._bonus_entry_repo.get_usable_by_abonent(
                abonent_id=abonent_id,
                at=datetime.combine(period_end, time.max, tzinfo=UTC),
            )
            for entry in bonus_entries:
                if entry.amount and entry.amount.currency.value == "RUB":
                    available_bonus += entry.amount

        # Сначала рассчитываем все суммы
        calculated_withdraws = []
        credit_amount = Money.zero("RUB")
        non_credit_amount = Money.zero("RUB")
        for service in services:
            cost_per_day = Money(service.cost / 30, service.currency)

            amount = self._billing_engine.calculate_withdraw(
                cost_per_day=cost_per_day,
                period_start=period_start,
                period_end=period_end,
            )

            service_bonus = (
                available_bonus
                if available_bonus.currency == amount.currency
                else Money.zero(amount.currency.value)
            )
            charge = self._billing_engine.calculate_shm_charge(
                cost=amount,
                quantity=1,
                abonent_discount_percent=0
                if self._get_bool_attr(service, "no_discount")
                else self._get_metadata_decimal(
                    service,
                    "abonent_discount_percent",
                    default=Decimal("0"),
                ),
                service_discount_percent=0
                if self._get_bool_attr(service, "no_discount")
                else self._get_metadata_decimal(
                    service,
                    "service_discount_percent",
                    default=Decimal("0"),
                ),
                bonus_balance=service_bonus,
            )
            if available_bonus.currency == charge.bonus_used.currency:
                available_bonus = available_bonus - charge.bonus_used

            if not charge.total.is_zero():
                pay_in_credit = self._get_bool_attr(service, "pay_in_credit")
                if pay_in_credit:
                    credit_amount += charge.total
                else:
                    non_credit_amount += charge.total
                calculated_withdraws.append({
                    "service_id": service.id,
                    "amount": float(charge.total.amount),
                    "currency": charge.total.currency.value,
                    "subtotal": float(charge.subtotal.amount),
                    "discount": float(charge.discount.amount),
                    "bonus_used": float(charge.bonus_used.amount),
                    "pay_in_credit": pay_in_credit,
                })

        if not calculated_withdraws:
            return []

        # Проверяем достаточность баланса перед созданием списаний
        total_amount = sum(w["amount"] for w in calculated_withdraws)
        abonent = await self._abonent_repo.get(abonent_id)

        if abonent:
            if (
                not abonent.allow_negative
                and non_credit_amount > abonent.balance
            ):
                logger.warning(
                    "Insufficient balance for non-credit services",
                    abonent_id=abonent_id,
                    amount=float(non_credit_amount.amount),
                )
                return []

            try:
                abonent.change_balance(
                    Money(-total_amount, "RUB"),
                    reason="Billing cycle",
                    allow_credit=not credit_amount.is_zero(),
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

            invoice = await self._create_invoice_for_withdraws(
                abonent_id=abonent_id,
                period_start=period_start,
                period_end=period_end,
                withdraws=withdraws,
                total_amount=total_amount,
            )
            if invoice is not None:
                for withdraw in withdraws:
                    withdraw["invoice_id"] = invoice.id

            await self._consume_bonus_entries(
                bonus_entries=bonus_entries,
                amount=Money(
                    sum(w["bonus_used"] for w in calculated_withdraws),
                    "RUB",
                ),
            )
            await self._abonent_repo.save(abonent)
            return withdraws

        return []

    @staticmethod
    def _get_metadata(service: Any) -> dict:
        metadata = getattr(service, "metadata", None)
        if not isinstance(metadata, dict):
            metadata = None
        if metadata is None:
            metadata = getattr(service, "meta", None)
        if not isinstance(metadata, dict):
            return {}
        return metadata or {}

    @staticmethod
    def _get_bool_attr(service: Any, key: str) -> bool:
        return getattr(service, key, False) is True

    def _get_metadata_decimal(
        self,
        service: Any,
        key: str,
        default: Decimal,
    ) -> Decimal:
        value = self._get_metadata(service).get(key, default)
        try:
            return Decimal(str(value))
        except Exception:
            logger.warning(
                "Invalid billing metadata decimal",
                service_id=getattr(service, "id", None),
                key=key,
                value=value,
            )
            return default

    async def _consume_bonus_entries(
        self,
        bonus_entries: list,
        amount: Money,
    ) -> None:
        remaining = amount
        if remaining.is_zero():
            return

        for entry in bonus_entries:
            used = entry.consume(remaining)
            if not used.is_zero() and self._bonus_entry_repo is not None:
                await self._bonus_entry_repo.save(entry)
            remaining = remaining - used
            if remaining.is_zero():
                return

    async def run_billing_cycle(
        self,
        period_start: date,
        period_end: date,
        offset: int = 0,
        limit: int = 100,
    ) -> dict:
        """Выполнить биллинг-цикл для пачки активных абонентов."""
        abonents = await self._abonent_repo.list_active(offset=offset, limit=limit)
        items: list[dict] = []
        withdraw_count = 0
        invoice_ids: set[UUID] = set()

        for abonent in abonents:
            withdraws = await self.run_billing_for_abonent(
                abonent_id=abonent.id,
                period_start=period_start,
                period_end=period_end,
            )
            withdraw_count += len(withdraws)
            for withdraw in withdraws:
                invoice_id = withdraw.get("invoice_id")
                if invoice_id is not None:
                    invoice_ids.add(invoice_id)

            items.append({
                "abonent_id": abonent.id,
                "withdraw_count": len(withdraws),
                "invoice_ids": [
                    withdraw["invoice_id"]
                    for withdraw in withdraws
                    if withdraw.get("invoice_id") is not None
                ],
                "status": "processed" if withdraws else "skipped",
            })

        return {
            "period_start": period_start,
            "period_end": period_end,
            "offset": offset,
            "limit": limit,
            "processed": len(abonents),
            "withdraw_count": withdraw_count,
            "invoice_count": len(invoice_ids),
            "items": items,
        }

    async def _create_invoice_for_withdraws(
        self,
        abonent_id: UUID,
        period_start: date,
        period_end: date,
        withdraws: list[dict],
        total_amount: float,
    ) -> Invoice | None:
        if self._invoice_repo is None or not withdraws:
            return None

        currency = withdraws[0].get("currency", "RUB")
        invoice = Invoice(
            abonent_id=abonent_id,
            amount=total_amount,
            currency=currency,
            period_start=datetime.combine(period_start, time.min, tzinfo=UTC),
            period_end=datetime.combine(period_end, time.max, tzinfo=UTC),
            due_date=datetime.combine(period_end, time.max, tzinfo=UTC),
            description=f"Billing invoice for {period_start.isoformat()} - {period_end.isoformat()}",
            metadata={
                "source": "billing_cycle",
                "withdraw_ids": [str(withdraw["withdraw_id"]) for withdraw in withdraws],
                "service_ids": [str(withdraw["service_id"]) for withdraw in withdraws],
            },
        )
        invoice.issue()
        return await self._invoice_repo.save(invoice)

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
