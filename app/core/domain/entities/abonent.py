# =============================================================================
# shm-next — Abonent Entity
# =============================================================================
"""
Доменная сущность Абонент.

Агрегатный корень, содержащий основную информацию
о абоненте и бизнес-логику работы с балансом.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.domain.value_objects import AbonentStatus, Money


class AbonentCreate:
    """DTO для создания абонента."""

    def __init__(
        self,
        full_name: str,
        phone: str,
        account_number: str,
        balance: float = 0,
        currency: str = "RUB",
        allow_negative: bool = False,
        tariff_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.full_name = full_name
        self.phone = phone
        self.account_number = account_number
        self.balance = balance
        self.currency = currency
        self.allow_negative = allow_negative
        self.tariff_id = tariff_id
        self._meta = metadata or {}


class AbonentUpdate:
    """DTO для обновления абонента."""

    def __init__(
        self,
        full_name: str | None = None,
        phone: str | None = None,
        status: str | None = None,
        tariff_id: UUID | None = None,
        allow_negative: bool | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.full_name = full_name
        self.phone = phone
        self.status = status
        self.tariff_id = tariff_id
        self.allow_negative = allow_negative
        self._meta = metadata


class Abonent:
    """
    Абонент — агрегатный корень.

    Инварианты:
    - Телефон обязателен и уникален
    - Баланс не может быть отрицательным (если allow_negative=False)
    - Статус определяет доступность услуг
    """

    def __init__(
        self,
        id: UUID | None = None,
        full_name: str = "",
        phone: str = "",
        account_number: str = "",
        email: str | None = None,
        balance: Money | None = None,
        status: AbonentStatus = AbonentStatus.ACTIVE,
        allow_negative: bool = False,
        tariff_id: UUID | None = None,
        password_hash: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
    ) -> None:
        self._id = id or uuid4()
        self._full_name = full_name
        self._phone = phone
        self._account_number = account_number
        self._email = email
        self._balance = balance or Money(0, "RUB")
        self._status = status
        self._allow_negative = allow_negative
        self._tariff_id = tariff_id
        self._password_hash = password_hash
        self._created_at = created_at or datetime.now(UTC)
        self._updated_at = updated_at or datetime.now(UTC)
        self._version = version

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def phone(self) -> str:
        return self._phone

    @property
    def account_number(self) -> str:
        return self._account_number

    @property
    def email(self) -> str | None:
        return self._email

    @property
    def balance(self) -> Money:
        return self._balance

    @property
    def status(self) -> AbonentStatus:
        return self._status

    @property
    def allow_negative(self) -> bool:
        return self._allow_negative

    @property
    def tariff_id(self) -> UUID | None:
        return self._tariff_id

    @property
    def password_hash(self) -> str | None:
        return self._password_hash

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version


    def update_info(self, full_name: str | None = None, phone: str | None = None, account_number: str | None = None) -> None:
        """Обновить основные данные абонента."""
        if full_name:
            self._full_name = full_name
        if phone:
            self._phone = phone
        if account_number:
            self._account_number = account_number
        self._updated_at = datetime.now(UTC)
        self._version += 1


    def assign_tariff(self, tariff_id: UUID) -> None:
        """Назначить тариф абоненту."""
        self._tariff_id = tariff_id
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def change_balance(
        self,
        amount: Money,
        reason: str = "",
        allow_credit: bool = False,
    ) -> None:
        """
        Изменить баланс абонента.

        Args:
            amount: Сумма изменения (может быть отрицательной)
            reason: Причина изменения

        Raises:
            ValueError: Если баланс станет отрицательным и это не разрешено
        """
        if amount.currency != self._balance.currency:
            raise ValueError("Currency mismatch")

        new_balance = self._balance + amount

        if new_balance.is_negative() and not self._allow_negative and not allow_credit:
            raise ValueError(
                f"Balance cannot be negative for abonent {self._id}"
            )

        self._balance = new_balance
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def activate(self) -> None:
        """Активировать абонента."""
        self._status = AbonentStatus.ACTIVE
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def block(self) -> None:
        """Заблокировать абонента."""
        self._status = AbonentStatus.BLOCKED
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def deactivate(self) -> None:
        """Деактивировать абонента."""
        self._status = AbonentStatus.DISABLED
        self._updated_at = datetime.now(UTC)
        self._version += 1
