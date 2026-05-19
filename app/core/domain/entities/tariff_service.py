# =============================================================================
# shm-next — TariffService Entity
# =============================================================================
"""
Услуга в составе тарифа.

Связывает услугу с тарифом, определяет стоимость
и условия подключения внутри тарифа.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.domain.value_objects import Money


class TariffService:
    """
    Услуга тарифа — связывает услугу с тарифом.

    Attributes:
        id: Идентификатор записи.
        tariff_id: ID тарифа.
        service_type: Тип услуги (voice, data, sms и т.д.).
        cost: Стоимость услуги в период.
        billing_period: Периодичность списания (monthly, daily и т.д.).
        is_optional: Является ли услуга опциональной.
        sort_order: Порядок отображения.
    """

    def __init__(
        self,
        id: UUID | None = None,
        tariff_id: UUID | None = None,
        service_type: str = "",
        name: str | None = None,
        cost: Money | None = None,
        billing_period: str = "monthly",
        is_optional: bool = False,
        sort_order: int = 0,
        currency: str = "RUB",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
    ) -> None:
        self._id = id or uuid4()
        self._tariff_id = tariff_id
        self._service_type = service_type
        self._name = name or service_type
        self._cost = cost
        self._billing_period = billing_period
        self._is_optional = is_optional
        self._sort_order = sort_order
        self._currency = currency
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
    def tariff_id(self) -> UUID | None:
        return self._tariff_id

    @property
    def service_type(self) -> str:
        return self._service_type

    @property
    def name(self) -> str:
        return self._name

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def cost(self) -> Money | None:
        return self._cost

    @property
    def billing_period(self) -> str:
        return self._billing_period

    @property
    def is_optional(self) -> bool:
        return self._is_optional

    @property
    def sort_order(self) -> int:
        return self._sort_order

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

    def update_cost(self, new_cost: Money) -> None:
        """Обновить стоимость услуги."""
        self._cost = new_cost
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def set_sort_order(self, order: int) -> None:
        """Установить порядок отображения."""
        self._sort_order = order
        self._updated_at = datetime.now(UTC)
        self._version += 1
