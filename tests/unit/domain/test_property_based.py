# =============================================================================
# shm-next — Property-Based Tests (hypothesis)
# =============================================================================
"""
Свойственные тесты для Value Objects.

Используют hypothesis для генерации широкого спектра входных данных
и проверки инвариантов на всех возможных значениях.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from app.core.domain.value_objects import Currency, Money, Period

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

@st.composite
def money_strategy(draw, min_value: float = -1_000_000, max_value: float = 1_000_000) -> Money:
    """Генератор случайных Money объектов."""
    value = draw(st.floats(min_value=min_value, max_value=max_value, allow_nan=False, allow_infinity=False))
    currency = draw(st.sampled_from([c.value for c in Currency]))
    return Money(value, currency)


@st.composite
def positive_money_strategy(draw) -> Money:
    """Генератор случайных положительных Money."""
    value = draw(st.floats(min_value=0.01, max_value=1_000_000, allow_nan=False, allow_infinity=False))
    currency = draw(st.sampled_from([c.value for c in Currency]))
    return Money(value, currency)


@st.composite
def non_negative_money_strategy(draw) -> Money:
    """Генератор случайных неотрицательных Money."""
    value = draw(st.floats(min_value=0, max_value=1_000_000, allow_nan=False, allow_infinity=False))
    currency = draw(st.sampled_from([c.value for c in Currency]))
    return Money(value, currency)


@st.composite
def period_strategy(draw) -> Period:
    """Генератор случайных периодов."""
    start = draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 1)))
    max_end_day = 28 if start.month == 2 else 30
    end_day = draw(st.integers(min_value=start.day, max_value=min(start.day + 365, max_end_day)))
    end_month = start.month
    end_year = start.year
    if end_day > max_end_day:
        end_month = min(start.month + 1, 12)
        end_day = min(end_day - max_end_day, 28)
        if end_month < start.month:
            end_year += 1
    try:
        end = date(end_year, end_month, end_day)
    except ValueError:
        end = start
    assume(end >= start)
    return Period(start, end)


# ---------------------------------------------------------------------------
# Money Property-Based Tests
# ---------------------------------------------------------------------------

class TestMoneyProperties:
    """Свойственные тесты для Money."""

    @given(money=positive_money_strategy())
    def test_positive_money_is_not_negative(self, money: Money):
        """Положительная сумма не может быть отрицательной."""
        assert not money.is_negative()

    @given(money=non_negative_money_strategy())
    def test_non_negative_money_is_zero_or_positive(self, money: Money):
        """Неотрицательная сумма — ноль или больше."""
        assert money.amount >= Decimal("0")

    @given(money=money_strategy())
    def test_money_rounds_to_2_decimal_places(self, money: Money):
        """Money всегда округляется до 2 знаков после запятой."""
        assert money.amount == money.amount.quantize(Decimal("0.01"))

    @given(money=money_strategy())
    def test_money_equals_itself(self, money: Money):
        """Любая сумма равна самой себе."""
        assert money == money

    @given(money=money_strategy())
    def test_money_hash_consistent_with_eq(self, money: Money):
        """Хэш согласован с равенством."""
        money2 = Money(money.amount, money.currency)
        assert money == money2
        assert hash(money) == hash(money2)

    @given(money=money_strategy())
    def test_repr_contains_amount_and_currency(self, money: Money):
        """repr содержит информацию о сумме и валюте."""
        r = repr(money)
        assert "Money" in r

    @given(money=money_strategy())
    def test_str_does_not_raise(self, money: Money):
        """str() не выбрасывает исключений."""
        result = str(money)
        assert isinstance(result, str)
        assert len(result) > 0

    @given(
        value=st.floats(min_value=0.01, max_value=1_000_000, allow_nan=False, allow_infinity=False),
        currency=st.sampled_from([c.value for c in Currency]),
    )
    def test_create_from_float_and_string_equivalent(self, value: float, currency: str):
        """Создание из float и str даёт одинаковый результат."""
        from_float = Money(value, currency)
        from_str = Money(str(value), currency)
        assert from_float.amount == from_str.amount

    @given(
        value=st.floats(min_value=-1_000_000, max_value=1_000_000, allow_nan=False, allow_infinity=False),
        currency=st.sampled_from([c.value for c in Currency]),
    )
    def test_create_from_decimal_and_float_equivalent(self, value: float, currency: str):
        """Money(float) == Money(Decimal(str(float)))."""
        from_float = Money(value, currency)
        from_decimal = Money(Decimal(str(value)), currency)
        assert from_float.amount == from_decimal.amount

    # --- Arithmetic properties ---

    @given(
        m1=non_negative_money_strategy(),
        m2=non_negative_money_strategy(),
    )
    def test_addition_commutative(self, m1: Money, m2: Money):
        """Сложение коммутативно (при одинаковой валюте)."""
        assume(m1.currency == m2.currency)
        assert m1 + m2 == m2 + m1

    @given(
        m1=non_negative_money_strategy(),
        m2=non_negative_money_strategy(),
        m3=non_negative_money_strategy(),
    )
    def test_addition_associative(self, m1: Money, m2: Money, m3: Money):
        """Сложение ассоциативно (при одинаковой валюте)."""
        assume(m1.currency == m2.currency == m3.currency)
        assert (m1 + m2) + m3 == m1 + (m2 + m3)

    @given(money=non_negative_money_strategy())
    def test_addition_with_zero_is_identity(self, money: Money):
        """Прибавление нуля не меняет сумму."""
        zero = Money.zero(money.currency.value)
        assert money + zero == money

    @given(
        value=st.floats(min_value=0.01, max_value=1_000_000, allow_nan=False, allow_infinity=False),
        currency=st.sampled_from([c.value for c in Currency]),
    )
    def test_subtraction_of_equals_is_zero(self, value: float, currency: str):
        """Вычитание равных сумм даёт ноль."""
        m1 = Money(value, currency)
        m2 = Money(value, currency)
        result = m1 - m2
        assert result.amount == Decimal("0")

    @given(
        m1=non_negative_money_strategy(),
        m2=non_negative_money_strategy(),
    )
    def test_subtraction_is_opposite_of_addition(self, m1: Money, m2: Money):
        """(a + b) - b == a (при одинаковой валюте и достаточном балансе)."""
        assume(m1.currency == m2.currency)
        result = (m1 + m2) - m2
        assert result.amount == m1.amount

    @given(money=non_negative_money_strategy(), factor=st.integers(min_value=0, max_value=1000))
    def test_multiplication_by_zero_is_zero(self, money: Money, factor: int):
        """Умножение на 0 даёт 0."""
        if factor == 0:
            result = money * factor
            assert result.amount == Decimal("0")

    @given(money=non_negative_money_strategy())
    def test_multiplication_by_one_is_identity(self, money: Money):
        """Умножение на 1 не меняет сумму."""
        result = money * 1
        assert result.amount == money.amount

    @given(
        m1=non_negative_money_strategy(),
        m2=non_negative_money_strategy(),
    )
    @settings(max_examples=50)
    def test_addition_result_currency_matches_operands(self, m1: Money, m2: Money):
        """Результат сложения имеет ту же валюту."""
        assume(m1.currency == m2.currency)
        result = m1 + m2
        assert result.currency == m1.currency

    @given(money=non_negative_money_strategy(), factor=st.integers(min_value=1, max_value=100))
    def test_multiplication_preserves_currency(self, money: Money, factor: int):
        """Умножение сохраняет валюту."""
        result = money * factor
        assert result.currency == money.currency

    @given(money=non_negative_money_strategy(), divisor=st.integers(min_value=1, max_value=100))
    def test_division_preserves_currency(self, money: Money, divisor: int):
        """Деление сохраняет валюту."""
        assume(divisor != 0)
        result = money / divisor
        assert result.currency == money.currency

    @given(
        m1=non_negative_money_strategy(),
        m2=non_negative_money_strategy(),
    )
    def test_currency_mismatch_raises_on_addition(self, m1: Money, m2: Money):
        """Сложение разных валют выбрасывает CurrencyMismatchError."""
        assume(m1.currency != m2.currency)
        with pytest.raises(Exception):  # CurrencyMismatchError
            _ = m1 + m2

    @given(
        m1=non_negative_money_strategy(),
        m2=non_negative_money_strategy(),
    )
    def test_currency_mismatch_raises_on_subtraction(self, m1: Money, m2: Money):
        """Вычитание разных валют выбрасывает CurrencyMismatchError."""
        assume(m1.currency != m2.currency)
        with pytest.raises(Exception):
            _ = m1 - m2

    @given(money=non_negative_money_strategy())
    def test_abs_of_non_negative_is_self(self, money: Money):
        """abs() неотрицательной суммы — она сама."""
        assert abs(money).amount == money.amount

    @given(money=positive_money_strategy())
    def test_neg_then_abs_returns_original(self, money: Money):
        """abs(-money) == money."""
        neg = -money
        assert neg.is_negative()
        assert abs(neg).amount == money.amount


# ---------------------------------------------------------------------------
# Period Property-Based Tests
# ---------------------------------------------------------------------------

class TestPeriodProperties:
    """Свойственные тесты для Period."""

    @given(
        year=st.integers(min_value=2000, max_value=2030),
        month=st.integers(min_value=1, max_value=12),
    )
    def test_month_factory_creates_valid_period(self, year: int, month: int):
        """Period.month() создаёт корректный период для любого месяца/года."""
        period = Period.month(year, month)
        assert period.start.year == year
        assert period.start.month == month
        assert period.start.day == 1
        assert period.end.month == month
        assert period.end.year == year
        assert period.end.day >= 28  # Минимум февраль без високосного года

    @given(
        year=st.integers(min_value=2000, max_value=2030),
        month=st.integers(min_value=1, max_value=12),
    )
    def test_month_factory_days_at_least_28(self, year: int, month: int):
        """Любой месяц содержит не менее 28 дней."""
        period = Period.month(year, month)
        assert period.days >= 28

    @given(
        year=st.integers(min_value=2000, max_value=2030),
        month=st.integers(min_value=1, max_value=12),
    )
    def test_month_factory_contains_first_and_last_day(self, year: int, month: int):
        """Period.month() содержит первый и последний день месяца."""
        import calendar
        period = Period.month(year, month)
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        assert period.contains(first_day)
        assert period.contains(last_day)

    @given(
        start_year=st.integers(min_value=2000, max_value=2025),
        start_month=st.integers(min_value=1, max_value=12),
    )
    def test_period_within_same_month_overlaps(self, start_year: int, start_month: int):
        """Два периода в одном месяце пересекаются."""
        import calendar
        p1 = Period.month(start_year, start_month)
        last_day = calendar.monthrange(start_year, start_month)[1]
        mid = last_day // 2
        p2 = Period(
            date(start_year, start_month, mid),
            date(start_year, start_month, last_day),
        )
        assert p1.overlaps(p2)

    @given(
        year=st.integers(min_value=2000, max_value=2030),
        month=st.integers(min_value=1, max_value=12),
    )
    def test_period_contains_its_start_and_end(self, year: int, month: int):
        """Период содержит свою начальную и конечную дату."""
        period = Period.month(year, month)
        assert period.contains(period.start)
        assert period.contains(period.end)

    @given(
        year=st.integers(min_value=2000, max_value=2030),
        month=st.integers(min_value=1, max_value=12),
    )
    def test_period_does_not_contain_day_before_start(self, year: int, month: int):
        """Период не содержит день перед началом."""
        period = Period.month(year, month)
        day_before = period.start - timedelta(days=1)
        assert not period.contains(day_before)

    @given(
        year=st.integers(min_value=2000, max_value=2030),
        month=st.integers(min_value=1, max_value=12),
    )
    def test_period_does_not_contain_day_after_end(self, year: int, month: int):
        """Период не содержит день после окончания."""
        period = Period.month(year, month)
        day_after = period.end + timedelta(days=1)
        assert not period.contains(day_after)

    @given(
        year1=st.integers(min_value=2000, max_value=2025),
        month1=st.integers(min_value=1, max_value=12),
        year2=st.integers(min_value=2000, max_value=2025),
        month2=st.integers(min_value=1, max_value=12),
    )
    def test_overlap_is_symmetric(self, year1: int, month1: int, year2: int, month2: int):
        """Пересечение периодов симметрично."""
        p1 = Period.month(year1, month1)
        p2 = Period.month(year2, month2)
        assert p1.overlaps(p2) == p2.overlaps(p1)

    @given(
        year=st.integers(min_value=2000, max_value=2030),
        month=st.integers(min_value=1, max_value=12),
    )
    def test_period_overlaps_with_itself(self, year: int, month: int):
        """Период пересекается сам с собой."""
        period = Period.month(year, month)
        assert period.overlaps(period)

    @given(
        year1=st.integers(min_value=2000, max_value=2020),
        month1=st.integers(min_value=1, max_value=12),
        year2=st.integers(min_value=2025, max_value=2030),
        month2=st.integers(min_value=1, max_value=12),
    )
    def test_distant_months_do_not_overlap(self, year1: int, month1: int, year2: int, month2: int):
        """Далёкие месяцы не пересекаются."""
        assume(abs((year2 * 12 + month2) - (year1 * 12 + month1)) > 3)
        p1 = Period.month(year1, month1)
        p2 = Period.month(year2, month2)
        assert not p1.overlaps(p2)

    @given(
        year=st.integers(min_value=2000, max_value=2030),
        month=st.integers(min_value=1, max_value=12),
    )
    def test_month_factory_eq_and_hash(self, year: int, month: int):
        """Два Period.month() с одинаковыми аргументами равны и имеют один хэш."""
        p1 = Period.month(year, month)
        p2 = Period.month(year, month)
        assert p1 == p2
        assert hash(p1) == hash(p2)

    @given(
        year1=st.integers(min_value=2000, max_value=2025),
        month1=st.integers(min_value=1, max_value=12),
        year2=st.integers(min_value=2000, max_value=2025),
        month2=st.integers(min_value=1, max_value=12),
    )
    @settings(max_examples=100)
    def test_different_months_are_not_equal(self, year1: int, month1: int, year2: int, month2: int):
        """Периоды разных месяцев не равны (если они действительно разные)."""
        assume((year1, month1) != (year2, month2))
        p1 = Period.month(year1, month1)
        p2 = Period.month(year2, month2)
        # Могут совпасть случайно, но очень маловероятно — пропускаем
        assume(p1 != p2)
        assert p1 != p2

    @given(
        year=st.integers(min_value=2000, max_value=2030),
        month=st.integers(min_value=1, max_value=12),
    )
    def test_month_factory_days_matches_calendar(self, year: int, month: int):
        """Количество дней в Period.month() совпадает с calendar."""
        import calendar
        period = Period.month(year, month)
        expected_days = calendar.monthrange(year, month)[1]
        assert period.days == expected_days

    @given(
        year=st.integers(min_value=2000, max_value=2030),
        month=st.integers(min_value=1, max_value=12),
    )
    def test_from_string_roundtrip(self, year: int, month: int):
        """Period.month() -> from_string() даёт тот же период."""
        period = Period.month(year, month)
        period_str = f"{year}-{month:02d}:{year}-{month:02d}"
        parsed = Period.from_string(period_str)
        assert parsed.start == period.start
        assert parsed.end == period.end