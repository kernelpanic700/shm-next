# =============================================================================
# shm-next — Invoice Entity
# =============================================================================
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4


class InvoiceStatus:
    """Статусы счёта."""
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    SENT = "SENT"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class Invoice:
    """
    Счёт — финансовый документ.

    Генерируется периодически для каждого абонента
    на основе списаний за период.
    """

    def __init__(
        self,
        id: UUID | None = None,
        abonent_id: UUID | None = None,
        amount: float = 0,
        currency: str = "RUB",
        status: str = InvoiceStatus.DRAFT,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
        due_date: datetime | None = None,
        description: str | None = None,
        metadata: dict | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
    ) -> None:
        self._id = id or uuid4()
        self._abonent_id = abonent_id
        self._amount = amount
        self._currency = currency
        self._status = status
        self._period_start = period_start
        self._period_end = period_end
        self._due_date = due_date
        self._description = description
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
    def amount(self) -> float:
        return self._amount

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def status(self) -> str:
        return self._status

    @property
    def period_start(self) -> datetime | None:
        return self._period_start

    @property
    def period_end(self) -> datetime | None:
        return self._period_end

    @property
    def due_date(self) -> datetime | None:
        return self._due_date

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def meta(self) -> dict:
        return self._meta

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version

    def issue(self) -> None:
        """Выставить счёт."""
        self._status = InvoiceStatus.ISSUED
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def mark_sent(self) -> None:
        """Отметить счёт как отправленный абоненту."""
        self._status = InvoiceStatus.SENT
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def mark_paid(self) -> None:
        """Отметить как оплаченный."""
        self._status = InvoiceStatus.PAID
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def mark_unpaid(self) -> None:
        """Вернуть счёт в состояние выставленного после возврата оплаты."""
        self._status = InvoiceStatus.ISSUED
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def mark_overdue(self) -> None:
        """Отметить как просроченный."""
        self._status = InvoiceStatus.OVERDUE
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def cancel(self) -> None:
        """Отменить счёт."""
        self._status = InvoiceStatus.CANCELLED
        self._updated_at = datetime.now(UTC)
        self._version += 1
