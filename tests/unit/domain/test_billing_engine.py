# =============================================================================
# shm-next — Unit Tests: Billing Engine
# =============================================================================
"""Тесты для BillingEngine."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.core.domain.value_objects import Money
from app.core.services.billing_engine import BillingEngine


class TestBillingEngine:
    """Тесты BillingEngine."""

    def setup_method(self):
        self.engine = BillingEngine(strategy="honest")

    def test_calculate_honest(self):
        cost_per_day = Money(10, "RUB")
        result = self.engine.calculate_withdraw(
            cost_per_day=cost_per_day,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            strategy="honest",
        )
        assert result.amount == Decimal("310")  # 10 * 31

    def test_calculate_monthly(self):
        cost_per_day = Money(10, "RUB")
        result = self.engine.calculate_withdraw(
            cost_per_day=cost_per_day,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            strategy="monthly",
        )
        assert result.amount > 0

    def test_calculate_prepaid(self):
        cost_per_day = Money(10, "RUB")
        result = self.engine.calculate_withdraw(
            cost_per_day=cost_per_day,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            strategy="prepaid",
        )
        assert result.amount == Decimal("310")

    def test_calculate_recurring_monthly(self):
        monthly_cost = Money(1000, "RUB")
        result = self.engine.calculate_recurring(monthly_cost, "monthly")
        assert result.amount == 1000

    def test_calculate_recurring_quarterly(self):
        monthly_cost = Money(1000, "RUB")
        result = self.engine.calculate_recurring(monthly_cost, "quarterly")
        assert result.amount == 3000

    def test_calculate_recurring_yearly(self):
        monthly_cost = Money(1000, "RUB")
        result = self.engine.calculate_recurring(monthly_cost, "yearly")
        assert result.amount == 12000

    def test_calculate_penalty(self):
        overdue = Money(1000, "RUB")
        penalty = self.engine.calculate_penalty(overdue, days_overdue=10, penalty_rate=0.01)
        assert penalty.amount == Decimal("100")  # 1000 * 0.01 * 10

    def test_calculate_penalty_zero_days(self):
        overdue = Money(1000, "RUB")
        penalty = self.engine.calculate_penalty(overdue, days_overdue=0)
        assert penalty.amount == 0
