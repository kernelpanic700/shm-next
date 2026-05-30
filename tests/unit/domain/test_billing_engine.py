# =============================================================================
# shm-next — Unit Tests: Billing Engine
# =============================================================================
"""Тесты для BillingEngine."""

from __future__ import annotations

from datetime import date
from datetime import datetime
from decimal import Decimal

from app.core.domain.value_objects import Money
from app.core.services.billing_engine import BillingEngine, SHMBillingMode, SHMPeriod


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

    def test_parse_shm_period_cost_months_days_hours(self):
        assert self.engine.parse_shm_period_cost("12") == SHMPeriod(months=12)
        assert self.engine.parse_shm_period_cost("0.01") == SHMPeriod(days=1)
        assert self.engine.parse_shm_period_cost("0.0001") == SHMPeriod(hours=1)
        assert self.engine.parse_shm_period_cost("0.10") == SHMPeriod(days=10)
        assert self.engine.parse_shm_period_cost("0.1001") == SHMPeriod(days=10, hours=1)
        assert self.engine.parse_shm_period_cost("1.1012") == SHMPeriod(months=1, days=10, hours=12)

    def test_calculate_shm_charge_with_discounts_and_bonus(self):
        result = self.engine.calculate_shm_charge(
            cost=Money("300", "RUB"),
            quantity=2,
            abonent_discount_percent=10,
            service_discount_percent=5,
            bonus_balance=Money("100", "RUB"),
        )

        assert result.subtotal.amount == Decimal("600.00")
        assert result.discount.amount == Decimal("90.00")
        assert result.bonus_used.amount == Decimal("100.00")
        assert result.total.amount == Decimal("410.00")

    def test_calculate_shm_charge_full_bonus_payment(self):
        result = self.engine.calculate_shm_charge(
            cost=Money("300", "RUB"),
            bonus_balance=Money("500", "RUB"),
        )

        assert result.bonus_used.amount == Decimal("300.00")
        assert result.total.amount == Decimal("0.00")

    def test_calculate_shm_fixed_30_days_end_at(self):
        starts_at = datetime(2026, 1, 10, 12, 0, 0)

        ends_at = self.engine.calculate_shm_end_at(
            starts_at=starts_at,
            period_cost="1.1012",
            mode=SHMBillingMode.FIXED_30_DAYS,
        )

        assert ends_at == datetime(2026, 2, 20, 0, 0, 0)

    def test_calculate_shm_calendar_end_at(self):
        starts_at = datetime(2026, 1, 31, 10, 0, 0)

        ends_at = self.engine.calculate_shm_end_at(
            starts_at=starts_at,
            period_cost="1",
            mode=SHMBillingMode.CALENDAR,
        )

        assert ends_at == datetime(2026, 2, 28, 10, 0, 0)

    def test_calculate_shm_end_of_month_end_at(self):
        starts_at = datetime(2026, 1, 10, 10, 0, 0)

        ends_at = self.engine.calculate_shm_end_at(
            starts_at=starts_at,
            period_cost="1",
            mode=SHMBillingMode.END_OF_MONTH,
        )

        assert ends_at == datetime(2026, 1, 31, 10, 0, 0)

    def test_calculate_shm_refund(self):
        refund = self.engine.calculate_shm_refund(
            cost=Money("300", "RUB"),
            starts_at=datetime(2026, 1, 1, 0, 0, 0),
            ends_at=datetime(2026, 1, 31, 0, 0, 0),
            stopped_at=datetime(2026, 1, 11, 0, 0, 0),
        )

        assert refund.used.amount == Decimal("100.00")
        assert refund.refund.amount == Decimal("200.00")
