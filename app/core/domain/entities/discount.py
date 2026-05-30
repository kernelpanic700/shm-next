# =============================================================================
# shm-next — Discount Entity
# =============================================================================
"""
Скидка — доменная сущность.

Представляет скидку, применимую к абоненту или услуге.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from app.core.domain.value_objects import Money


class DiscountType(StrEnum):
    PERCENT = 'percent'
    FIXED = 'fixed'
    RELATIVE = 'relative'


class Discount:
    """
    Скидка.

    Attributes:
        id: Идентификатор скидки.
        name: Название скидки.
        description: Описание.
        discount_type: Тип скидки (percent, fixed, relative).
        value: Значение скидки (процент или сумма).
        currency: Валюта (для фиксированных скидок).
        valid_from: Дата начала действия.
        valid_to: Дата окончания действия.
        is_active: Активна ли скидка.
        max_uses: Максимальное количество использований (None = безлимитно).
        used_count: Текущее количество использований.
    """

    def __init__(
        self,
        id: UUID | None = None,
        name: str = "",
        description: str = "",
        discount_type: str = "percent",
        value: float = 0.0,
        currency: str = "RUB",
        valid_from: datetime | None = None,
        valid_to: datetime | None = None,
        is_active: bool = True,
        max_uses: int | None = None,
        used_count: int = 0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
    ) -> None:
        self._id = id or uuid4()
        self._name = name
        self._description = description
        self._discount_type = discount_type
        self._value = value
        self._currency = currency
        self._valid_from = valid_from
        self._valid_to = valid_to
        self._is_active = is_active
        self._max_uses = max_uses
        self._used_count = used_count
        self._created_at = created_at or datetime.now(UTC)
        self._updated_at = updated_at or datetime.now(UTC)
        self._version = version

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def discount_type(self) -> str:
        return self._discount_type

    @property
    def value(self) -> float:
        return self._value

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def valid_from(self) -> datetime | None:
        return self._valid_from

    @property
    def valid_to(self) -> datetime | None:
        return self._valid_to

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def max_uses(self) -> int | None:
        return self._max_uses

    @property
    def used_count(self) -> int:
        return self._used_count

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version

    # ------------------------------------------------------------------
    # Business methods
    # ------------------------------------------------------------------

    def is_valid_at(self, dt: datetime) -> bool:
        """Проверяет, действует ли скидка в указанный момент времени."""
        from datetime import UTC

        if not self._is_active:
            return False

        # Normalize datetimes for comparison
        check_dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt

        valid_from = self._valid_from
        if valid_from and valid_from.tzinfo is None:
            valid_from = valid_from.replace(tzinfo=UTC)

        valid_to = self._valid_to
        if valid_to and valid_to.tzinfo is None:
            valid_to = valid_to.replace(tzinfo=UTC)

        if valid_from and check_dt < valid_from:
            return False
        if valid_to and check_dt > valid_to:
            return False
        if self._max_uses is not None and self._used_count >= self._max_uses:
            return False
        return True

    def apply_to(self, amount: Money) -> Money:
        """
        Применить скидку к сумме.

        Args:
            amount: Исходная сумма.

        Returns:
            Сумма со скидкой.

        Raises:
            ValueError: Если скидка неактивна или истекла.
        """
        from datetime import datetime

        now = datetime.now(UTC)
        if not self.is_valid_at(now):
            raise ValueError("Скидка не может быть применена: недействительна")

        if self._discount_type == "percent":
            discount_amount = amount * (self._value / 100)
            result = amount - discount_amount
        elif self._discount_type == "fixed":
            discount_amount = Money(self._value, self._currency)
            result = amount - discount_amount
        elif self._discount_type == "relative":
            result = amount * (1 - self._value / 100)
        else:
            raise ValueError(f"Неизвестный тип скидки: {self._discount_type}")

        # Результат не может быть отрицательным
        if result.is_negative():
            result = Money.zero(amount.currency)

        return result

    def increment_usage(self) -> None:
        """Увеличить счётчик использований."""
        self._used_count += 1
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def deactivate(self) -> None:
        """Деактивировать скидку."""
        self._is_active = False
        self._updated_at = datetime.now(UTC)
        self._version += 1
