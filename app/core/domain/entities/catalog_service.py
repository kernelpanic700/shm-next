# =============================================================================
# shm-next - CatalogService Entity
# =============================================================================
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.core.domain.value_objects import Money


class CatalogService:
    """
    Каталожная услуга SHM.

    Это аналог строки из классической таблицы SHM `services`: описание услуги,
    стоимость, период, правила заказа, переходы на следующую услугу и состав
    дочерних услуг для композитных пакетов.
    """

    def __init__(
        self,
        id: UUID | None = None,
        name: str = "",
        cost: Money | None = None,
        period_cost: Decimal | float | str = Decimal("1.0000"),
        category: str | None = None,
        children: list[UUID] | None = None,
        next_service_id: UUID | None = None,
        legacy_service_id: int | None = None,
        allow_to_order: bool = True,
        max_count: int | None = None,
        question: bool = False,
        pay_always: bool = False,
        no_discount: bool = False,
        description: str | None = None,
        pay_in_credit: bool = False,
        config: dict | None = None,
        is_composite: bool = False,
        is_deleted: bool = False,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
    ) -> None:
        self._id = id or uuid4()
        self._name = name.strip()
        self._cost = cost or Money.zero()
        self._period_cost = Decimal(str(period_cost)).quantize(Decimal("0.0001"))
        self._category = category
        self._children = children or []
        self._next_service_id = next_service_id
        self._legacy_service_id = legacy_service_id
        self._allow_to_order = allow_to_order
        self._max_count = max_count
        self._question = question
        self._pay_always = pay_always
        self._no_discount = no_discount
        self._description = description
        self._pay_in_credit = pay_in_credit
        self._config = config or {}
        self._is_composite = is_composite
        self._is_deleted = is_deleted
        self._created_at = created_at or datetime.now(UTC)
        self._updated_at = updated_at or datetime.now(UTC)
        self._version = version
        self._validate()

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def cost(self) -> Money:
        return self._cost

    @property
    def period_cost(self) -> Decimal:
        return self._period_cost

    @property
    def category(self) -> str | None:
        return self._category

    @property
    def children(self) -> list[UUID]:
        return list(self._children)

    @property
    def next_service_id(self) -> UUID | None:
        return self._next_service_id

    @property
    def legacy_service_id(self) -> int | None:
        return self._legacy_service_id

    @property
    def allow_to_order(self) -> bool:
        return self._allow_to_order and not self._is_deleted

    @property
    def max_count(self) -> int | None:
        return self._max_count

    @property
    def question(self) -> bool:
        return self._question

    @property
    def pay_always(self) -> bool:
        return self._pay_always

    @property
    def no_discount(self) -> bool:
        return self._no_discount

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def pay_in_credit(self) -> bool:
        return self._pay_in_credit

    @property
    def config(self) -> dict:
        return dict(self._config)

    @property
    def is_composite(self) -> bool:
        return self._is_composite

    @property
    def is_deleted(self) -> bool:
        return self._is_deleted

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version

    def mark_deleted(self) -> None:
        self._is_deleted = True
        self._allow_to_order = False
        self._touch()

    def update_price(self, cost: Money, period_cost: Decimal | float | str) -> None:
        self._cost = cost
        self._period_cost = Decimal(str(period_cost)).quantize(Decimal("0.0001"))
        self._validate()
        self._touch()

    def set_children(self, children: list[UUID]) -> None:
        self._children = list(children)
        self._is_composite = bool(children)
        self._touch()

    def _touch(self) -> None:
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def _validate(self) -> None:
        if not self._name:
            raise ValueError("Catalog service name is required")
        if self._cost.is_negative():
            raise ValueError("Catalog service cost cannot be negative")
        if self._period_cost < 0:
            raise ValueError("Catalog service period_cost cannot be negative")
        if self._max_count is not None and self._max_count < 1:
            raise ValueError("Catalog service max_count must be positive")
