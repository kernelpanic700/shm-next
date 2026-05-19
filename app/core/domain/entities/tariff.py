# =============================================================================
# shm-next — Tariff Entity
# =============================================================================
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4


class Tariff:
    """
    Тариф — агрегатный корень.

    Содержит набор услуг и pricing-правила.
    """

    def __init__(
        self,
        id: UUID | None = None,
        name: str = "",
        description: str = "",
        services: list[dict] | None = None,
        is_active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
        price: float = 0,
        currency: str = "RUB",
        billing_period: str = "monthly",
    ) -> None:
        self._id = id or uuid4()
        self._name = name
        self._description = description
        self._services = services or []
        self._is_active = is_active
        self._created_at = created_at or datetime.now(UTC)
        self._updated_at = updated_at or datetime.now(UTC)
        self._version = version
        self._price = price
        self._currency = currency
        self._billing_period = billing_period

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value

    @property
    def services(self) -> list[dict]:
        return self._services

    @services.setter
    def services(self, value: list[dict]) -> None:
        self._services = value

    @property
    def is_active(self) -> bool:
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self._is_active = value
        self._updated_at = datetime.now(UTC)
        self._version += 1

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        self._price = value
        self._updated_at = datetime.now(UTC)
        self._version += 1

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def billing_period(self) -> str:
        return self._billing_period

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version
