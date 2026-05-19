# =============================================================================
# shm-next — Money Value Object
# =============================================================================
"""
Денежная сумма как Value Object.

Использует Decimal для точных вычислений.
Поддерживает основные арифметические операции.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.core.domain.value_objects.currency import Currency


class CurrencyMismatchError(Exception):
    """Ошибка несовпадения валют при операциях с Money."""
    pass


class Money:
    """
    Денежная сумма.

    Инварианты:
    - Сумма округляется до 2 знаков после запятой
    - Валюта обязательна
    - Арифметические операции только с одинаковой валютой
    """

    def __init__(
        self,
        amount: Decimal | float | str,
        currency: Currency | str = "RUB",
    ) -> None:
        if isinstance(currency, str):
            currency = Currency(currency)
        self._amount = Decimal(str(amount)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        self._currency = currency

    @classmethod
    def zero(cls, currency: str = "RUB") -> Money:
        """Создать нулевую сумму."""
        return cls(Decimal("0"), currency)

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def currency(self) -> Currency:
        return self._currency

    def is_negative(self) -> bool:
        return self._amount < 0

    def is_zero(self) -> bool:
        return self._amount == 0

    def __add__(self, other: Any) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return Money(self._amount + other._amount, self._currency)

    def __sub__(self, other: Any) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return Money(self._amount - other._amount, self._currency)

    def __mul__(self, other: Any) -> Money:
        if isinstance(other, (int, float, Decimal)):
            return Money(self._amount * Decimal(str(other)), self._currency)
        return NotImplemented

    def __truediv__(self, other: Any) -> Money:
        if isinstance(other, (int, float, Decimal)):
            return Money(self._amount / Decimal(str(other)), self._currency)
        return NotImplemented

    def __abs__(self) -> Money:
        return Money(abs(self._amount), self._currency)

    def __neg__(self) -> Money:
        return Money(-self._amount, self._currency)

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return self._amount < other._amount

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return self._amount <= other._amount

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return self._amount > other._amount

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return self._amount >= other._amount

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self._amount == other._amount and self._currency == other._currency

    def __hash__(self) -> int:
        return hash((self._amount, self._currency))

    def __repr__(self) -> str:
        return f"Money({self._amount}, '{self._currency}')"

    def __str__(self) -> str:
        symbols = {"RUB": "₽", "USD": "$", "EUR": "€"}
        symbol = symbols.get(self._currency.value, self._currency.value)
        return f"{self._amount} {symbol}"

    def _check_currency(self, other: Money) -> None:
        if self._currency != other._currency:
            raise CurrencyMismatchError(
                f"Cannot operate on different currencies: "
                f"{self._currency} != {other._currency}"
            )
