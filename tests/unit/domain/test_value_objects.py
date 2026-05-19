# =============================================================================
# shm-next — Unit Tests: Value Objects
# =============================================================================
"""Тесты для Value Objects."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.core.domain.value_objects import (
    AbonentStatus,
    Currency,
    CurrencyMismatchError,
    EventCategory,
    EventType,
    Money,
    PaymentStatus,
    Period,
    ServiceStatus,
    SpoolStatus,
)


class TestMoney:
    """Тесты Money Value Object."""

    def test_create_from_float(self):
        money = Money(100.50, "RUB")
        assert money.amount == Decimal("100.50")
        assert money.currency == Currency.RUB

    def test_create_from_string(self):
        money = Money("99.99", "USD")
        assert money.amount == Decimal("99.99")

    def test_create_from_decimal(self):
        money = Money(Decimal("50.25"), "EUR")
        assert money.amount == Decimal("50.25")

    def test_zero(self):
        money = Money.zero("RUB")
        assert money.amount == Decimal("0")
        assert money.is_zero()

    def test_addition(self):
        m1 = Money(100, "RUB")
        m2 = Money(50, "RUB")
        result = m1 + m2
        assert result.amount == Decimal("150")

    def test_subtraction(self):
        m1 = Money(100, "RUB")
        m2 = Money(30, "RUB")
        result = m1 - m2
        assert result.amount == Decimal("70")

    def test_multiplication(self):
        money = Money(100, "RUB")
        result = money * 2
        assert result.amount == Decimal("200")

    def test_division(self):
        money = Money(100, "RUB")
        result = money / 2
        assert result.amount == Decimal("50")

    def test_comparison(self):
        m1 = Money(100, "RUB")
        m2 = Money(200, "RUB")
        assert m1 < m2
        assert m2 > m1
        assert m1 <= m2
        assert m2 >= m1

    def test_equality(self):
        m1 = Money(100, "RUB")
        m2 = Money(100, "RUB")
        m3 = Money(100, "USD")
        assert m1 == m2
        assert m1 != m3

    def test_currency_mismatch_on_add(self):
        m1 = Money(100, "RUB")
        m2 = Money(50, "USD")
        with pytest.raises(CurrencyMismatchError):
            _ = m1 + m2

    def test_is_negative(self):
        assert Money(-10, "RUB").is_negative()
        assert not Money(10, "RUB").is_negative()

    def test_abs(self):
        money = Money(-50, "RUB")
        assert abs(money).amount == Decimal("50")

    def test_neg(self):
        money = Money(50, "RUB")
        neg = -money
        assert neg.amount == Decimal("-50")

    def test_repr(self):
        money = Money(100, "RUB")
        assert "Money" in repr(money)
        assert "100" in repr(money)


class TestCurrency:
    """Тесты Currency Value Object."""

    def test_rub_decimal_places(self):
        assert Currency.RUB.decimal_places == 2

    def test_usd_decimal_places(self):
        assert Currency.USD.decimal_places == 2

    def test_enum_values(self):
        assert Currency.RUB.value == "RUB"
        assert Currency.USD.value == "USD"


class TestAbonentStatus:
    """Тесты AbonentStatus."""

    def test_active_status(self):
        assert AbonentStatus.ACTIVE.is_active()
        assert not AbonentStatus.BLOCKED.is_active()

    def test_values(self):
        assert AbonentStatus.ACTIVE.value == "ACTIVE"
        assert AbonentStatus.BLOCKED.value == "BLOCKED"


class TestServiceStatus:
    """Тесты ServiceStatus."""

    def test_values(self):
        assert ServiceStatus.ACTIVE.value == "ACTIVE"
        assert ServiceStatus.INIT.value == "INIT"


class TestPaymentStatus:
    """Тесты PaymentStatus."""

    def test_values(self):
        assert PaymentStatus.NEW.value == "NEW"
        assert PaymentStatus.COMPLETED.value == "COMPLETED"
        assert PaymentStatus.REFUNDED.value == "REFUNDED"


class TestSpoolStatus:
    """Тесты SpoolStatus."""

    def test_values(self):
        assert SpoolStatus.NEW.value == "NEW"
        assert SpoolStatus.PROCESSING.value == "PROCESSING"
        assert SpoolStatus.STUCK.value == "STUCK"


class TestEventType:
    """Тесты EventType."""

    def test_category(self):
        assert EventType.ABONENT_CREATED.category() == EventCategory.ACCOUNT
        assert EventType.PAYMENT_COMPLETED.category() == EventCategory.PAYMENT

    def test_is_critical(self):
        assert EventType.ABONENT_DELETED.is_critical() is True
        assert EventType.ABONENT_CREATED.is_critical() is False


class TestPeriod:
    """Тесты Period Value Object."""

    def test_create(self):
        from datetime import date
        period = Period(date(2024, 1, 1), date(2024, 1, 31))
        assert period.start == date(2024, 1, 1)
        assert period.end == date(2024, 1, 31)

    def test_days(self):
        from datetime import date
        period = Period(date(2024, 1, 1), date(2024, 1, 31))
        assert period.days == 31

    def test_invalid_period(self):
        from datetime import date
        with pytest.raises(ValueError):
            Period(date(2024, 2, 1), date(2024, 1, 1))

    def test_contains(self):
        from datetime import date
        period = Period(date(2024, 1, 1), date(2024, 1, 31))
        assert period.contains(date(2024, 1, 15))
        assert not period.contains(date(2024, 2, 1))

    def test_overlaps(self):
        from datetime import date
        p1 = Period(date(2024, 1, 1), date(2024, 1, 31))
        p2 = Period(date(2024, 1, 15), date(2024, 2, 15))
        p3 = Period(date(2024, 3, 1), date(2024, 3, 31))
        assert p1.overlaps(p2)
        assert not p1.overlaps(p3)

    def test_month_factory(self):
        period = Period.month(2024, 2)
        assert period.start.day == 1
        assert period.end.day == 29  # 2024 is a leap year

    def test_eq_and_hash(self):
        from datetime import date
        p1 = Period(date(2024, 1, 1), date(2024, 1, 31))
        p2 = Period(date(2024, 1, 1), date(2024, 1, 31))
        p3 = Period(date(2024, 2, 1), date(2024, 2, 28))
        assert p1 == p2
        assert p1 != p3
        assert hash(p1) == hash(p2)
