# =============================================================================
# shm-next — BonusEntry Entity
# =============================================================================
"""
Бонусная запись — начисление бонусов абоненту.

Бонусы могут начисляться за платежи, подключение услуг,
участие в акциях и т.д.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.domain.value_objects import Money


class BonusEntry:
    """
    Бонусная запись.

    Attributes:
        id: Идентификатор записи.
        abonent_id: ID абонента.
        amount: Сумма бонуса.
        reason: Причина начисления.
        expires_at: Дата истечения срока действия бонуса.
        is_active: Активен ли бонус.
        source: Источник начисления (ручное, автоматическое, акция и т.д.).
    """

    def __init__(
        self,
        id: UUID | None = None,
        abonent_id: UUID | None = None,
        amount: Money | None = None,
        reason: str = "",
        expires_at: datetime | None = None,
        is_active: bool = True,
        source: str = "manual",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
    ) -> None:
        self._id = id or uuid4()
        self._abonent_id = abonent_id
        self._amount = amount
        self._reason = reason
        self._expires_at = expires_at
        self._is_active = is_active
        self._source = source
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
    def abonent_id(self) -> UUID | None:
        return self._abonent_id

    @property
    def amount(self) -> Money | None:
        return self._amount

    @property
    def reason(self) -> str:
        return self._reason

    @property
    def expires_at(self) -> datetime | None:
        return self._expires_at

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def source(self) -> str:
        return self._source

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

    def is_expired(self, at: datetime | None = None) -> bool:
        """Проверяет, истёк ли срок действия бонуса."""
        check_date = at or datetime.now(UTC)
        if self._expires_at is None:
            return False
        expires_at = self._expires_at
        if check_date.tzinfo is None:
            check_date = check_date.replace(tzinfo=UTC)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return check_date > expires_at

    def expire(self) -> None:
        """Принудительно деактивировать бонус."""
        self._is_active = False
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def can_use(self, at: datetime | None = None) -> bool:
        """Проверяет, можно ли использовать бонус."""
        if not self._is_active:
            return False
        if self.is_expired(at):
            return False
        return True

    def consume(self, amount: Money) -> Money:
        """Списать часть бонуса и вернуть фактически использованную сумму."""
        if self._amount is None:
            return Money.zero(amount.currency.value)
        if amount.currency != self._amount.currency:
            raise ValueError("Bonus currency mismatch")
        if amount.is_negative():
            raise ValueError("Consumed bonus amount cannot be negative")
        if amount.is_zero() or not self.can_use():
            return Money.zero(amount.currency.value)

        used = self._amount if self._amount <= amount else amount
        self._amount = self._amount - used
        if self._amount.is_zero():
            self._is_active = False
        self._updated_at = datetime.now(UTC)
        self._version += 1
        return used
