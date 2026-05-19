# =============================================================================
# shm-next — UserService Entity
# =============================================================================
from __future__ import annotations

from datetime import UTC, datetime
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
        status: ServiceStatus = ServiceStatus.INIT,
        activated_at: datetime | None = None,
        deactivated_at: datetime | None = None,
        cost: float = 0,
        currency: str = "RUB",
        metadata: dict | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
    ) -> None:
        self._id = id or uuid4()
        self._abonent_id = abonent_id
        self._service_type = service_type
        self._tariff_service_id = tariff_service_id
        self._status = status
        self._activated_at = activated_at
        self._deactivated_at = deactivated_at
        self._cost = cost
        self._currency = currency
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
    def cost(self) -> float:
        return self._cost

    @property
    def currency(self) -> str:
        return self._currency

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

    def activate(self) -> None:
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
        self._activated_at = datetime.now(UTC)
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
