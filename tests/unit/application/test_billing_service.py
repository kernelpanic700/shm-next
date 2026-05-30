# =============================================================================
# shm-next — BillingService Tests
# =============================================================================
"""Тесты для BillingService (application layer)."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.application.billing.billing_service import BillingService
from app.core.domain.entities.abonent import Abonent
from app.core.domain.entities.bonus_entry import BonusEntry
from app.core.domain.entities.invoice import InvoiceStatus
from app.core.domain.value_objects import Money


class TestBillingServiceGetBalance:
    """Тесты получения баланса."""

    def setup_method(self):
        self.abonent_repo = AsyncMock()
        self.billing_repo = AsyncMock()
        self.service_repo = AsyncMock()
        self.withdraw_repo = AsyncMock()
        self.event_bus = AsyncMock()
        self.service = BillingService(
            abonent_repo=self.abonent_repo,
            billing_repo=self.billing_repo,
            service_repo=self.service_repo,
            withdraw_repo=self.withdraw_repo,
            event_bus=self.event_bus,
        )

    @pytest.mark.asyncio
    async def test_get_balance_found(self):
        """Получение баланса — абонент найден."""
        abonent = Abonent(
            id=uuid4(),
            full_name="Тест",
            balance=Money(1500.0, "RUB"),
            allow_negative=False,
        )
        self.abonent_repo.get.return_value = abonent

        result = await self.service.get_balance(abonent.id)

        assert result["balance"] == 1500.0
        assert result["currency"] == "RUB"
        assert result["available"] is True
        assert result["allow_negative"] is False

    @pytest.mark.asyncio
    async def test_get_balance_negative_but_allowed(self):
        """Баланс отрицательный, но allow_negative=True."""
        abonent = Abonent(
            id=uuid4(),
            full_name="Тест",
            balance=Money(-100.0, "RUB"),
            allow_negative=True,
        )
        self.abonent_repo.get.return_value = abonent

        result = await self.service.get_balance(abonent.id)

        assert result["balance"] == -100.0
        assert result["available"] is True

    @pytest.mark.asyncio
    async def test_get_balance_not_found(self):
        """Абонент не найден — ошибка."""
        self.abonent_repo.get.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await self.service.get_balance(uuid4())


class TestBillingServiceCalculateWithdraw:
    """Тесты расчёта списания."""

    def setup_method(self):
        self.abonent_repo = AsyncMock()
        self.billing_repo = AsyncMock()
        self.service_repo = AsyncMock()
        self.withdraw_repo = AsyncMock()
        self.event_bus = AsyncMock()
        self.service = BillingService(
            abonent_repo=self.abonent_repo,
            billing_repo=self.billing_repo,
            service_repo=self.service_repo,
            withdraw_repo=self.withdraw_repo,
            event_bus=self.event_bus,
        )

    @pytest.mark.asyncio
    async def test_calculate_withdraw_success(self):
        """Расчёт списания — успешный расчёт."""
        abonent_id = uuid4()
        service_id = uuid4()

        mock_service = MagicMock()
        mock_service.id = service_id
        mock_service.cost = 3000.0
        mock_service.currency = "RUB"

        self.billing_repo.get_abonent_services.return_value = [mock_service]

        result = await self.service.calculate_withdraw(
            abonent_id=abonent_id,
            service_id=service_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
        )

        assert isinstance(result, object)  # Money object
        assert float(result.amount) > 0

    @pytest.mark.asyncio
    async def test_calculate_withdraw_service_not_found(self):
        """Расчёт списания — услуга не найдена."""
        self.billing_repo.get_abonent_services.return_value = []

        with pytest.raises(ValueError, match="not found or not active"):
            await self.service.calculate_withdraw(
                abonent_id=uuid4(),
                service_id=uuid4(),
                period_start=date(2025, 1, 1),
                period_end=date(2025, 1, 31),
            )


class TestBillingServiceRunBilling:
    """Тесты выполнения биллинга."""

    def setup_method(self):
        self.abonent_repo = AsyncMock()
        self.billing_repo = AsyncMock()
        self.service_repo = AsyncMock()
        self.withdraw_repo = AsyncMock()
        self.event_bus = AsyncMock()
        self.service = BillingService(
            abonent_repo=self.abonent_repo,
            billing_repo=self.billing_repo,
            service_repo=self.service_repo,
            withdraw_repo=self.withdraw_repo,
            event_bus=self.event_bus,
        )

    @pytest.mark.asyncio
    async def test_run_billing_for_abonent_with_services(self):
        """Биллинг для абонента с активными услугами."""
        abonent_id = uuid4()
        service_id = uuid4()

        abonent = Abonent(
            id=abonent_id,
            full_name="Тест",
            balance=Money(5000.0, "RUB"),
        )

        mock_service = MagicMock()
        mock_service.id = service_id
        mock_service.cost = 1000.0
        mock_service.currency = "RUB"

        self.abonent_repo.get.return_value = abonent
        self.billing_repo.get_abonent_services.return_value = [mock_service]
        self.withdraw_repo.create_withdraw.return_value = uuid4()

        result = await self.service.run_billing_for_abonent(
            abonent_id=abonent_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["service_id"] == service_id

    @pytest.mark.asyncio
    async def test_run_billing_for_abonent_creates_invoice_when_repo_provided(self):
        """Биллинг создаёт счёт на сумму списаний, если подключён invoice_repo."""
        abonent_id = uuid4()
        service_id = uuid4()
        withdraw_id = uuid4()
        invoice_repo = AsyncMock()

        abonent = Abonent(
            id=abonent_id,
            full_name="Тест",
            balance=Money(5000.0, "RUB"),
        )

        mock_service = MagicMock()
        mock_service.id = service_id
        mock_service.cost = 1000.0
        mock_service.currency = "RUB"

        self.abonent_repo.get.return_value = abonent
        self.billing_repo.get_abonent_services.return_value = [mock_service]
        self.withdraw_repo.create_withdraw.return_value = withdraw_id
        invoice_repo.save.side_effect = lambda invoice: invoice
        service = BillingService(
            abonent_repo=self.abonent_repo,
            billing_repo=self.billing_repo,
            service_repo=self.service_repo,
            withdraw_repo=self.withdraw_repo,
            event_bus=self.event_bus,
            invoice_repo=invoice_repo,
        )

        result = await service.run_billing_for_abonent(
            abonent_id=abonent_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
        )

        invoice = invoice_repo.save.call_args.args[0]
        assert invoice.abonent_id == abonent_id
        assert invoice.status == InvoiceStatus.ISSUED
        assert invoice.amount == sum(item["amount"] for item in result)
        assert invoice.period_start.date() == date(2025, 1, 1)
        assert invoice.period_end.date() == date(2025, 1, 31)
        assert invoice.meta["source"] == "billing_cycle"
        assert invoice.meta["withdraw_ids"] == [str(withdraw_id)]
        assert result[0]["invoice_id"] == invoice.id

    @pytest.mark.asyncio
    async def test_run_billing_no_active_services(self):
        """Биллинг без активных услуг — пустой результат."""
        abonent_id = uuid4()

        abonent = Abonent(
            id=abonent_id,
            full_name="Тест",
            balance=Money(1000.0, "RUB"),
        )

        self.abonent_repo.get.return_value = abonent
        self.billing_repo.get_abonent_services.return_value = []

        result = await self.service.run_billing_for_abonent(
            abonent_id=abonent_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_run_billing_insufficient_balance(self):
        """Биллинг при недостаточном балансе — списание не создаётся."""
        abonent_id = uuid4()
        service_id = uuid4()

        abonent = Abonent(
            id=abonent_id,
            full_name="Тест",
            balance=Money(10.0, "RUB"),
            allow_negative=False,
        )

        mock_service = MagicMock()
        mock_service.id = service_id
        mock_service.cost = 1000.0
        mock_service.currency = "RUB"

        self.abonent_repo.get.return_value = abonent
        self.billing_repo.get_abonent_services.return_value = [mock_service]

        await self.service.run_billing_for_abonent(
            abonent_id=abonent_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
        )

        # Списание не должно быть создано из-за недостаточного баланса
        self.withdraw_repo.create_withdraw.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_billing_cycle_processes_active_abonents(self):
        """Биллинг-цикл обрабатывает пачку активных абонентов."""
        abonent_id = uuid4()
        service_id = uuid4()
        invoice_repo = AsyncMock()
        withdraw_id = uuid4()
        abonent = Abonent(
            id=abonent_id,
            full_name="Тест",
            balance=Money(5000.0, "RUB"),
        )
        mock_service = MagicMock()
        mock_service.id = service_id
        mock_service.cost = 300.0
        mock_service.currency = "RUB"

        self.abonent_repo.list_active.return_value = [abonent]
        self.abonent_repo.get.return_value = abonent
        self.billing_repo.get_abonent_services.return_value = [mock_service]
        self.withdraw_repo.create_withdraw.return_value = withdraw_id
        invoice_repo.save.side_effect = lambda invoice: invoice
        service = BillingService(
            abonent_repo=self.abonent_repo,
            billing_repo=self.billing_repo,
            service_repo=self.service_repo,
            withdraw_repo=self.withdraw_repo,
            event_bus=self.event_bus,
            invoice_repo=invoice_repo,
        )

        result = await service.run_billing_cycle(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 1),
            offset=10,
            limit=25,
        )

        assert result["processed"] == 1
        assert result["withdraw_count"] == 1
        assert result["invoice_count"] == 1
        assert result["offset"] == 10
        assert result["limit"] == 25
        assert result["items"][0]["abonent_id"] == abonent_id
        assert result["items"][0]["status"] == "processed"
        assert len(result["items"][0]["invoice_ids"]) == 1
        self.abonent_repo.list_active.assert_awaited_once_with(offset=10, limit=25)

    @pytest.mark.asyncio
    async def test_run_billing_cycle_reports_skipped_without_withdraws(self):
        """Биллинг-цикл помечает абонента как skipped, если списаний нет."""
        abonent = Abonent(
            id=uuid4(),
            full_name="Тест",
            balance=Money(5000.0, "RUB"),
        )
        self.abonent_repo.list_active.return_value = [abonent]
        self.abonent_repo.get.return_value = abonent
        self.billing_repo.get_abonent_services.return_value = []

        result = await self.service.run_billing_cycle(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
        )

        assert result["processed"] == 1
        assert result["withdraw_count"] == 0
        assert result["invoice_count"] == 0
        assert result["items"][0]["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_run_billing_applies_service_discounts_and_bonus_entries(self):
        """Биллинг применяет скидки из metadata и списывает бонусы."""
        abonent_id = uuid4()
        service_id = uuid4()
        bonus_repo = AsyncMock()
        bonus_entry = BonusEntry(
            abonent_id=abonent_id,
            amount=Money("5.00", "RUB"),
            reason="promo",
        )
        abonent = Abonent(
            id=abonent_id,
            full_name="Тест",
            balance=Money("1000.00", "RUB"),
        )
        mock_service = MagicMock()
        mock_service.id = service_id
        mock_service.cost = 300.0
        mock_service.currency = "RUB"
        mock_service.no_discount = False
        mock_service.pay_in_credit = False
        mock_service.metadata = {
            "abonent_discount_percent": 10,
            "service_discount_percent": 10,
        }
        withdraw_id = uuid4()

        self.abonent_repo.get.return_value = abonent
        self.billing_repo.get_abonent_services.return_value = [mock_service]
        self.withdraw_repo.create_withdraw.return_value = withdraw_id
        bonus_repo.get_usable_by_abonent.return_value = [bonus_entry]
        service = BillingService(
            abonent_repo=self.abonent_repo,
            billing_repo=self.billing_repo,
            service_repo=self.service_repo,
            withdraw_repo=self.withdraw_repo,
            event_bus=self.event_bus,
            bonus_entry_repo=bonus_repo,
        )

        result = await service.run_billing_for_abonent(
            abonent_id=abonent_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 1),
        )

        assert result[0]["amount"] == 3.0
        assert result[0]["subtotal"] == 10.0
        assert result[0]["discount"] == 2.0
        assert result[0]["bonus_used"] == 5.0
        assert bonus_entry.amount == Money("0.00", "RUB")
        assert bonus_entry.is_active is False
        bonus_repo.save.assert_awaited_once_with(bonus_entry)

    @pytest.mark.asyncio
    async def test_run_billing_allows_credit_only_for_credit_services(self):
        """Биллинг разрешает минус для pay_in_credit услуг."""
        abonent_id = uuid4()
        service_id = uuid4()
        abonent = Abonent(
            id=abonent_id,
            full_name="Тест",
            balance=Money("1.00", "RUB"),
            allow_negative=False,
        )
        mock_service = MagicMock()
        mock_service.id = service_id
        mock_service.cost = 300.0
        mock_service.currency = "RUB"
        mock_service.no_discount = False
        mock_service.pay_in_credit = True
        mock_service.metadata = {}

        self.abonent_repo.get.return_value = abonent
        self.billing_repo.get_abonent_services.return_value = [mock_service]
        self.withdraw_repo.create_withdraw.return_value = uuid4()

        result = await self.service.run_billing_for_abonent(
            abonent_id=abonent_id,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 1),
        )

        assert len(result) == 1
        assert result[0]["pay_in_credit"] is True
        assert abonent.balance == Money("-9.00", "RUB")


class TestBillingServiceHistory:
    """Тесты истории списаний и платежей."""

    def setup_method(self):
        self.abonent_repo = AsyncMock()
        self.billing_repo = AsyncMock()
        self.service_repo = AsyncMock()
        self.withdraw_repo = AsyncMock()
        self.event_bus = AsyncMock()
        self.service = BillingService(
            abonent_repo=self.abonent_repo,
            billing_repo=self.billing_repo,
            service_repo=self.service_repo,
            withdraw_repo=self.withdraw_repo,
            event_bus=self.event_bus,
        )

    @pytest.mark.asyncio
    async def test_get_withdraw_history(self):
        """Получение истории списаний."""
        self.withdraw_repo.get_by_abonent.return_value = []

        result = await self.service.get_withdraw_history(uuid4())

        assert result == []
        self.withdraw_repo.get_by_abonent.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tariff_info(self):
        """Получение информации о тарифе."""
        expected = {"name": "Basic", "price": 0}
        self.billing_repo.get_abonent_tariff.return_value = expected

        result = await self.service.get_abonent_tariff_info(uuid4())

        assert result == expected

    @pytest.mark.asyncio
    async def test_get_last_payment(self):
        """Получение последнего платежа."""
        expected = {"amount": 500.0}
        self.billing_repo.get_abonent_last_payment.return_value = expected

        result = await self.service.get_abonent_last_payment(uuid4())

        assert result == expected
