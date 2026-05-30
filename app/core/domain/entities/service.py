# =============================================================================
# shm-next — UserService Entity
# =============================================================================
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.core.domain.value_objects import ServiceStatus


class UserService:
    """
    Услуга абонента — агрегатный корень.

    Представляет подключённую услугу конкретного абонента.
    """

    def __init__(
        self,
        id: UUID | None = None,
        abonent_id: UUID | None = None,
        service_type: str = "",
        tariff_service_id: UUID | None = None,
        catalog_service_id: UUID | None = None,
        status: ServiceStatus = ServiceStatus.INIT,
        activated_at: datetime | None = None,
        deactivated_at: datetime | None = None,
        expire_at: datetime | None = None,
        cost: float = 0,
        currency: str = "RUB",
        period_cost: Decimal | float | str = Decimal("1.0000"),
        next_service_id: UUID | None = None,
        parent_id: UUID | None = None,
        quantity: int = 1,
        auto_bill: bool = True,
        pay_always: bool = False,
        pay_in_credit: bool = False,
        no_discount: bool = False,
        metadata: dict | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
    ) -> None:
        self._id = id or uuid4()
        self._abonent_id = abonent_id
        self._service_type = service_type
        self._tariff_service_id = tariff_service_id
        self._catalog_service_id = catalog_service_id
        self._status = status
        self._activated_at = activated_at
        self._deactivated_at = deactivated_at
        self._expire_at = expire_at
        self._cost = cost
        self._currency = currency
        self._period_cost = Decimal(str(period_cost)).quantize(Decimal("0.0001"))
        self._next_service_id = next_service_id
        self._parent_id = parent_id
        self._quantity = quantity
        self._auto_bill = auto_bill
        self._pay_always = pay_always
        self._pay_in_credit = pay_in_credit
        self._no_discount = no_discount
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
    def tariff_service_id(self) -> UUID | None:
        return self._tariff_service_id

    @property
    def catalog_service_id(self) -> UUID | None:
        return self._catalog_service_id

    @property
    def service_type(self) -> str:
        return self._service_type

    @property
    def status(self) -> ServiceStatus:
        return self._status

    @property
    def is_active(self) -> bool:
        return self._status.is_active()

    @property
    def activated_at(self) -> datetime | None:
        return self._activated_at

    @property
    def deactivated_at(self) -> datetime | None:
        return self._deactivated_at

    @property
    def expire_at(self) -> datetime | None:
        return self._expire_at

    @property
    def cost(self) -> float:
        return self._cost

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def period_cost(self) -> Decimal:
        return self._period_cost

    @property
    def next_service_id(self) -> UUID | None:
        return self._next_service_id

    @property
    def parent_id(self) -> UUID | None:
        return self._parent_id

    @property
    def quantity(self) -> int:
        return self._quantity

    @property
    def auto_bill(self) -> bool:
        return self._auto_bill

    @property
    def pay_always(self) -> bool:
        return self._pay_always

    @property
    def pay_in_credit(self) -> bool:
        return self._pay_in_credit

    @property
    def no_discount(self) -> bool:
        return self._no_discount

    @property
    def meta(self) -> dict:
        return self._meta

    @property
    def metadata(self) -> dict:
        """Alias for meta."""
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

    def activate(self, activated_at: datetime | None = None) -> None:
        """
        Активировать услугу.

        Raises:
            ValueError: Если услуга уже в терминальном или активном состоянии.
        """
        if self._status.is_terminal():
            raise ValueError(
                f"Cannot activate service in terminal state: {self._status}"
            )
        if self._status == ServiceStatus.ACTIVE:
            raise ValueError("Service is already active")
        self._status = ServiceStatus.ACTIVE
        self._activated_at = activated_at or datetime.now(UTC)
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def renew(self, expire_at: datetime, cost: float | None = None) -> None:
        """Продлить услугу до указанной даты."""
        if self._status.is_terminal():
            raise ValueError(f"Cannot renew service in terminal state: {self._status}")
        self._status = ServiceStatus.ACTIVE
        self._expire_at = expire_at
        if cost is not None:
            self._cost = cost
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def suspend(self, reason: str = "") -> None:
        """Приостановить услугу, например при нехватке средств."""
        if self._status.is_terminal():
            raise ValueError(f"Cannot suspend service in terminal state: {self._status}")
        self._status = ServiceStatus.SUSPENDED
        if reason:
            self._meta["suspend_reason"] = reason
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def deactivate(self, reason: str = "") -> None:
        """
        Деактивировать услугу.

        Raises:
            ValueError: Если услуга уже в терминальном состоянии.
        """
        if self._status.is_terminal():
            raise ValueError(
                f"Cannot deactivate service in terminal state: {self._status}"
            )
        self._status = ServiceStatus.DEACTIVATED
        self._deactivated_at = datetime.now(UTC)
        if reason:
            self._meta["deactivation_reason"] = reason
        self._updated_at = datetime.now(UTC)
        self._version += 1
