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

from datetime import date, timedelta
from decimal import Decimal

from app.core.domain.value_objects import Money, Period


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
