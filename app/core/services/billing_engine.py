# =============================================================================
# shm-next — Billing Engine
# =============================================================================
"""
Движок биллинга — расчёт списаний.

Реализует стратегии расчёта:
- honest: честный расчёт по дням
- monthly: помесячный расчёт
- prepaid: предоплата с вычетом
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from app.core.domain.value_objects import Money, Period


class SHMBillingMode(StrEnum):
    """Calculation modes used by classic SHM."""

    FIXED_30_DAYS = "fixed_30_days"
    CALENDAR = "calendar"
    END_OF_MONTH = "end_of_month"


@dataclass(frozen=True)
class SHMPeriod:
    """Parsed SHM period_cost value."""

    months: int = 0
    days: int = 0
    hours: int = 0

    @property
    def is_instant(self) -> bool:
        return self.months == 0 and self.days == 0 and self.hours == 0


@dataclass(frozen=True)
class SHMCharge:
    """Result of SHM-compatible service charge calculation."""

    subtotal: Money
    discount: Money
    bonus_used: Money
    total: Money


@dataclass(frozen=True)
class SHMRefund:
    """Result of early service termination calculation."""

    used: Money
    refund: Money


class BillingEngine:
    """
    Движок расчёта списаний.

    Стратегии расчёта:
    - honest: Ежедневное списание пропорционально дням
    - monthly: Помесячное списание
    - prepaid: Списание с предоплаты
    """

    STRATEGIES = {
        "honest": "_calculate_honest",
        "monthly": "_calculate_monthly",
        "prepaid": "_calculate_prepaid",
    }

    def __init__(self, strategy: str = "honest") -> None:
        self._strategy = strategy

    def calculate_withdraw(
        self,
        cost_per_day: Money,
        period_start: date,
        period_end: date,
        strategy: str | None = None,
    ) -> Money:
        """
        Рассчитать сумму списания.

        Args:
            cost_per_day: Стоимость в день
            period_start: Начало периода
            period_end: Конец периода
            strategy: Стратегия расчёта

        Returns:
            Money: Сумма списания
        """
        strategy = strategy or self._strategy
        method_name = self.STRATEGIES.get(strategy, "_calculate_honest")
        method = getattr(self, method_name)

        period = Period(period_start, period_end)
        return method(cost_per_day, period)

    def _calculate_honest(
        self,
        cost_per_day: Money,
        period: Period,
    ) -> Money:
        """
        Честное списание — пропорционально дням.

        Формула: cost_per_day * days_in_period
        """
        days = period.days
        return cost_per_day * days

    def _calculate_monthly(
        self,
        cost_per_day: Money,
        period: Period,
    ) -> Money:
        """
        Помесячное списание — полная стоимость за каждый начатый месяц.
        """
        from datetime import date as Date

        start = period.start
        end = period.end

        # Считаем количество полных месяцев
        months = (end.year - start.year) * 12 + (end.month - start.month) + 1

        # Стоимость за полный месяц
        if start.month == end.month and start.year == end.year:
            days_in_month = (
                Date(start.year, start.month + 1, 1) - timedelta(days=1)
            ).day if start.month < 12 else 31
            cost_per_month = cost_per_day * days_in_month
        else:
            # Средняя стоимость месяца
            cost_per_month = cost_per_day * 30

        return cost_per_month * months

    def _calculate_prepaid(
        self,
        cost_per_day: Money,
        period: Period,
    ) -> Money:
        """
        Списание с предоплаты — вычитаем из предоплаты.
        Если предоплаты недостаточно — списываем остаток.
        """
        return cost_per_day * period.days

    def calculate_recurring(
        self,
        monthly_cost: Money,
        billing_period: str = "monthly",
    ) -> Money:
        """
        Рассчитать рекуррентный платёж.

        Args:
            monthly_cost: Стоимость за период
            billing_period: Период биллинга (monthly, quarterly, yearly)

        Returns:
            Money: Сумма списания
        """
        multipliers = {
            "monthly": 1,
            "quarterly": 3,
            "semi-annual": 6,
            "yearly": 12,
        }
        multiplier = multipliers.get(billing_period, 1)
        return monthly_cost * multiplier

    def calculate_penalty(
        self,
        overdue_amount: Money,
        days_overdue: int,
        penalty_rate: float = 0.01,
    ) -> Money:
        """
        Рассчитать пеню за просрочку.

        Args:
            overdue_amount: Сумма задолженности
            days_overdue: Количество дней просрочки
            penalty_rate: Ставка пени (в день, по умолчанию 1%)

        Returns:
            Money: Сумма пени
        """
        penalty = overdue_amount * Decimal(str(penalty_rate)) * days_overdue
        return penalty

    # ------------------------------------------------------------------
    # SHM-compatible calculations
    # ------------------------------------------------------------------

    def parse_shm_period_cost(self, period_cost: Decimal | float | int | str) -> SHMPeriod:
        """
        Parse SHM `period_cost`.

        SHM encodes periods as months plus decimal day/hour suffix:
        - `12` -> 12 months
        - `0.01` -> 1 day
        - `0.0001` -> 1 hour
        - `0.1001` -> 10 days and 1 hour
        - `1.1012` -> 1 month, 10 days and 12 hours
        """
        raw = str(period_cost).strip()
        if not raw:
            raise ValueError("period_cost cannot be empty")
        if raw.startswith("-"):
            raise ValueError("period_cost cannot be negative")

        if "." not in raw:
            return SHMPeriod(months=int(raw or "0"))

        months_raw, fraction = raw.split(".", 1)
        months = int(months_raw or "0")
        fraction = fraction.rstrip("0") if fraction not in {"0", "00", "000", "0000"} else fraction

        if not fraction or set(fraction) == {"0"}:
            return SHMPeriod(months=months)

        day_digits = fraction[:2]
        hour_digits = fraction[2:4]

        if len(day_digits) == 1:
            days = int(day_digits) * 10
        else:
            days = int(day_digits)

        if not hour_digits:
            hours = 0
        elif len(hour_digits) == 1:
            hours = int(hour_digits) * 10
        else:
            hours = int(hour_digits)

        if days > 31:
            raise ValueError(f"Invalid SHM period days: {days}")
        if hours > 23:
            raise ValueError(f"Invalid SHM period hours: {hours}")
        return SHMPeriod(months=months, days=days, hours=hours)

    def calculate_shm_charge(
        self,
        cost: Money,
        quantity: Decimal | float | int | str = 1,
        abonent_discount_percent: Decimal | float | int | str = 0,
        service_discount_percent: Decimal | float | int | str = 0,
        bonus_balance: Money | None = None,
    ) -> SHMCharge:
        """
        Calculate SHM order/renewal charge.

        Formula follows SHM docs: `cost * qnt` minus client and service
        discounts, then bonuses are consumed before money balance.
        """
        quantity_decimal = Decimal(str(quantity))
        if quantity_decimal <= 0:
            raise ValueError("quantity must be positive")

        subtotal = cost * quantity_decimal
        discount_percent = Decimal(str(abonent_discount_percent)) + Decimal(str(service_discount_percent))
        if discount_percent < 0:
            raise ValueError("discount percent cannot be negative")
        if discount_percent > 100:
            discount_percent = Decimal("100")

        discount = subtotal * (discount_percent / Decimal("100"))
        after_discount = subtotal - discount

        bonus_balance = bonus_balance or Money.zero(cost.currency.value)
        if bonus_balance.currency != cost.currency:
            raise ValueError("bonus currency must match service currency")

        bonus_used = bonus_balance if bonus_balance <= after_discount else after_discount
        total = after_discount - bonus_used
        return SHMCharge(
            subtotal=subtotal,
            discount=discount,
            bonus_used=bonus_used,
            total=total,
        )

    def calculate_shm_end_at(
        self,
        starts_at: datetime,
        period_cost: Decimal | float | int | str,
        mode: SHMBillingMode | str = SHMBillingMode.FIXED_30_DAYS,
    ) -> datetime:
        """Calculate service expiration date according to SHM billing mode."""
        period = self.parse_shm_period_cost(period_cost)
        mode = SHMBillingMode(mode)

        if period.is_instant:
            return starts_at

        if mode == SHMBillingMode.FIXED_30_DAYS:
            return starts_at + timedelta(days=period.months * 30 + period.days, hours=period.hours)

        if mode == SHMBillingMode.END_OF_MONTH:
            base = self._add_months(starts_at, max(period.months - 1, 0)) if period.months else starts_at
            last_day = calendar.monthrange(base.year, base.month)[1]
            end = base.replace(day=last_day)
            return end + timedelta(days=period.days, hours=period.hours)

        end = self._add_months(starts_at, period.months) if period.months else starts_at
        return end + timedelta(days=period.days, hours=period.hours)

    def calculate_shm_refund(
        self,
        cost: Money,
        starts_at: datetime,
        ends_at: datetime,
        stopped_at: datetime,
        mode: SHMBillingMode | str = SHMBillingMode.FIXED_30_DAYS,
    ) -> SHMRefund:
        """Calculate used amount and refund for early service termination."""
        if ends_at <= starts_at:
            return SHMRefund(used=cost, refund=Money.zero(cost.currency.value))

        if stopped_at <= starts_at:
            return SHMRefund(used=Money.zero(cost.currency.value), refund=cost)
        if stopped_at >= ends_at:
            return SHMRefund(used=cost, refund=Money.zero(cost.currency.value))

        mode = SHMBillingMode(mode)
        if mode == SHMBillingMode.FIXED_30_DAYS:
            total_units = Decimal(str((ends_at - starts_at).total_seconds()))
            used_units = Decimal(str((stopped_at - starts_at).total_seconds()))
            used = cost * (used_units / total_units)
            return SHMRefund(used=used, refund=cost - used)

        # Calendar and end-of-month modes use actual elapsed time in the service period.
        total_units = Decimal(str((ends_at - starts_at).total_seconds()))
        used_units = Decimal(str((stopped_at - starts_at).total_seconds()))
        used = cost * (used_units / total_units)
        return SHMRefund(used=used, refund=cost - used)

    @staticmethod
    def _add_months(value: datetime, months: int) -> datetime:
        month_index = value.month - 1 + months
        year = value.year + month_index // 12
        month = month_index % 12 + 1
        day = min(value.day, calendar.monthrange(year, month)[1])
        return value.replace(year=year, month=month, day=day)
