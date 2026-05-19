# =============================================================================
# shm-next — Payment Entity
# =============================================================================
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.domain.value_objects import PaymentStatus


class Payment:
    """
    Платёж — агрегатный корень.

    Отслеживает lifecycle платежа от создания до завершения/возврата.
    """

    def __init__(
        self,
        id: UUID | None = None,
        abonent_id: UUID | None = None,
        amount: float = 0,
        currency: str = "RUB",
        payment_method: str = "cash",
        status: PaymentStatus = PaymentStatus.NEW,
        external_id: str | None = None,
        created_at: datetime | None = None,
        completed_at: datetime | None = None,
        metadata: dict | None = None,
        version: int = 1,
    ) -> None:
        self._id = id or uuid4()
        self._abonent_id = abonent_id
        self._amount = amount
        self._currency = currency
        self._payment_method = payment_method
        self._status = status
        self._external_id = external_id
        self._created_at = created_at or datetime.now(UTC)
        self._completed_at = completed_at
        self._meta = metadata or {}
        self._version = version

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def abonent_id(self) -> UUID | None:
        return self._abonent_id

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def payment_method(self) -> str:
        return self._payment_method

    @property
    def status(self) -> PaymentStatus:
        return self._status

    @property
    def external_id(self) -> str | None:
        return self._external_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def completed_at(self) -> datetime | None:
        return self._completed_at

    @property
    def meta(self) -> dict:
        return self._meta

    @property
    def metadata(self) -> dict:
        """Alias for meta property."""
        return self._meta

    @property
    def version(self) -> int:
        return self._version

    def confirm(self) -> None:
        """Подтвердить платёж."""
        self._status = PaymentStatus.COMPLETED
        self._completed_at = datetime.now(UTC)
        self._version += 1

    def refund(self) -> None:
        """Выполнить возврат."""
        self._status = PaymentStatus.REFUNDED
        self._completed_at = datetime.now(UTC)
        self._version += 1

    def fail(self, reason: str = "") -> None:
        """Отметить как неудачный."""
        self._status = PaymentStatus.FAILED
        if reason:
            self._meta["error"] = reason
        self._version += 1
