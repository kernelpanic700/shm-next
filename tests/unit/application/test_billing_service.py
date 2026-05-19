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
