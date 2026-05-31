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
        email: str | None = None,
        login: str | None = None,
        login2: str | None = None,
        partner_id: UUID | None = None,
        discount: float = 0,
        credit: float = 0,
        bonus: float = 0,
        comment: str | None = None,
        contract: str | None = None,
        can_overdraft: bool = False,
        verified: bool = False,
        metadata: dict | None = None,
    ) -> None:
        self.full_name = full_name
        self.phone = phone
        self.account_number = account_number
        self.balance = balance
        self.currency = currency
        self.allow_negative = allow_negative
        self.tariff_id = tariff_id
        self.email = email
        self.login = login
        self.login2 = login2
        self.partner_id = partner_id
        self.discount = discount
        self.credit = credit
        self.bonus = bonus
        self.comment = comment
        self.contract = contract
        self.can_overdraft = can_overdraft
        self.verified = verified
        self._meta = metadata or {}


class AbonentUpdate:
    """DTO для обновления абонента."""

    def __init__(
        self,
        full_name: str | None = None,
        phone: str | None = None,
        account_number: str | None = None,
        status: str | None = None,
        tariff_id: UUID | None = None,
        allow_negative: bool | None = None,
        email: str | None = None,
        login: str | None = None,
        login2: str | None = None,
        partner_id: UUID | None = None,
        discount: float | None = None,
        credit: float | None = None,
        bonus: float | None = None,
        comment: str | None = None,
        contract: str | None = None,
        can_overdraft: bool | None = None,
        verified: bool | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.full_name = full_name
        self.phone = phone
        self.account_number = account_number
        self.status = status
        self.tariff_id = tariff_id
        self.allow_negative = allow_negative
        self.email = email
        self.login = login
        self.login2 = login2
        self.partner_id = partner_id
        self.discount = discount
        self.credit = credit
        self.bonus = bonus
        self.comment = comment
        self.contract = contract
        self.can_overdraft = can_overdraft
        self.verified = verified
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
        login: str | None = None,
        login2: str | None = None,
        balance: Money | None = None,
        status: AbonentStatus = AbonentStatus.ACTIVE,
        allow_negative: bool = False,
        tariff_id: UUID | None = None,
        partner_id: UUID | None = None,
        discount: float = 0,
        credit: float = 0,
        bonus: float = 0,
        comment: str | None = None,
        contract: str | None = None,
        can_overdraft: bool = False,
        verified: bool = False,
        settings: dict | None = None,
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
        self._login = login
        self._login2 = login2
        self._balance = balance or Money(0, "RUB")
        self._status = status
        self._allow_negative = allow_negative
        self._tariff_id = tariff_id
        self._partner_id = partner_id
        self._discount = discount
        self._credit = credit
        self._bonus = bonus
        self._comment = comment
        self._contract = contract
        self._can_overdraft = can_overdraft
        self._verified = verified
        self._settings = settings or {}
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
    def login(self) -> str | None:
        return self._login

    @property
    def login2(self) -> str | None:
        return self._login2

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
    def partner_id(self) -> UUID | None:
        return self._partner_id

    @property
    def discount(self) -> float:
        return self._discount

    @property
    def credit(self) -> float:
        return self._credit

    @property
    def bonus(self) -> float:
        return self._bonus

    @property
    def comment(self) -> str | None:
        return self._comment

    @property
    def contract(self) -> str | None:
        return self._contract

    @property
    def can_overdraft(self) -> bool:
        return self._can_overdraft

    @property
    def verified(self) -> bool:
        return self._verified

    @property
    def settings(self) -> dict:
        return self._settings

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
