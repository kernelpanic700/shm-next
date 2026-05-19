# =============================================================================
# shm-next — Withdraw Entity
# =============================================================================
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.domain.value_objects import WithdrawStatus


class Withdraw:
    """
    Списание — агрегатный корень.

    Отслеживает списание средств за услуги.
    """

    def __init__(
        self,
        id: UUID | None = None,
        abonent_id: UUID | None = None,
        service_id: UUID | None = None,
        amount: float = 0,
        currency: str = "RUB",
        status: str = WithdrawStatus.PENDING,
        strategy: str = "honest",
        completed_at: datetime | None = None,
        error_message: str | None = None,
        metadata: dict | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
    ) -> None:
        self._id = id or uuid4()
        self._abonent_id = abonent_id
        self._service_id = service_id
        self._amount = amount
        self._currency = currency
        self._status = status
        self._strategy = strategy
        self._completed_at = completed_at
        self._error_message = error_message
        self._meta = metadata or {}
        self._created_at = created_at or datetime.now(UTC)
        self._updated_at = updated_at or datetime.now(UTC)
        self._version = version

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def abonent_id(self) -> UUID | None:
        return self._abonent_id

    @property
    def service_id(self) -> UUID | None:
        return self._service_id

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def status(self) -> str:
        return self._status

    @property
    def strategy(self) -> str:
        return self._strategy

    @property
    def completed_at(self) -> datetime | None:
        return self._completed_at

    @property
    def error_message(self) -> str | None:
        return self._error_message

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version

    @property
    def meta(self) -> dict:
        """Alias for metadata."""
        return self._meta

    @property
    def metadata(self) -> dict:
        """Alias for meta."""
        return self._meta

    def complete(self) -> None:
        """Завершить списание."""
        self._status = WithdrawStatus.COMPLETED
        self._completed_at = datetime.now(UTC)
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def fail(self, error: str) -> None:
        """Отметить как неудачное."""
        self._status = WithdrawStatus.FAILED
        self._error_message = error
        self._updated_at = datetime.now(UTC)
        self._version += 1
