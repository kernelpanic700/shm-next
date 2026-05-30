from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from litestar.exceptions import HTTPException

from app.api.dto.requests import DiscountCreateRequest, DiscountUpdateRequest
from app.api.v1.discounts import DiscountController
from app.core.domain.entities.discount import Discount


class FakeDiscountRepo:
    def __init__(self, discounts: list[Discount] | None = None) -> None:
        self.discounts = discounts or []
        self.saved: list[Discount] = []

    async def get(self, discount_id):
        return next(
            (discount for discount in self.discounts if discount.id == discount_id),
            None,
        )

    async def get_active(self):
        return [discount for discount in self.discounts if discount.is_active]

    async def get_valid_at(self, dt):
        return [discount for discount in self.discounts if discount.is_valid_at(dt)]

    async def save(self, discount):
        self.saved.append(discount)
        self.discounts = [
            existing for existing in self.discounts if existing.id != discount.id
        ]
        self.discounts.append(discount)
        return discount


class FakeUnitOfWork:
    def __init__(self, discounts: list[Discount] | None = None) -> None:
        self.discounts = FakeDiscountRepo(discounts)
        self.commit_count = 0

    async def commit(self):
        self.commit_count += 1


@pytest.mark.asyncio
async def test_create_discount() -> None:
    uow = FakeUnitOfWork()

    response = await DiscountController.create_discount.fn(
        None,
        data=DiscountCreateRequest(
            name="Promo",
            discount_type="percent",
            value=Decimal("15"),
            valid_to=datetime.now(UTC) + timedelta(days=30),
        ),
        uow=uow,
    )

    assert response.name == "Promo"
    assert response.value == 15.0
    assert response.is_active is True
    assert uow.commit_count == 1


@pytest.mark.asyncio
async def test_list_valid_discounts() -> None:
    valid = Discount(
        name="Valid",
        value=10,
        valid_to=datetime.now(UTC) + timedelta(days=1),
    )
    expired = Discount(
        name="Expired",
        value=20,
        valid_to=datetime.now(UTC) - timedelta(days=1),
    )
    uow = FakeUnitOfWork([valid, expired])

    response = await DiscountController.list_discounts.fn(
        None,
        uow=uow,
        valid_now=True,
    )

    assert response.total == 1
    assert response.items[0].id == valid.id


@pytest.mark.asyncio
async def test_update_discount() -> None:
    discount = Discount(name="Old", value=5)
    uow = FakeUnitOfWork([discount])

    response = await DiscountController.update_discount.fn(
        None,
        discount_id=discount.id,
        data=DiscountUpdateRequest(name="New", value=Decimal("7")),
        uow=uow,
    )

    assert response.name == "New"
    assert response.value == 7.0
    assert response.used_count == discount.used_count
    assert uow.commit_count == 1


@pytest.mark.asyncio
async def test_deactivate_discount() -> None:
    discount = Discount(name="Promo", value=5)
    uow = FakeUnitOfWork([discount])

    response = await DiscountController.deactivate_discount.fn(
        None,
        discount_id=discount.id,
        uow=uow,
    )

    assert response.is_active is False
    assert uow.commit_count == 1


@pytest.mark.asyncio
async def test_get_discount_returns_404() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await DiscountController.get_discount.fn(
            None,
            discount_id=uuid4(),
            uow=FakeUnitOfWork(),
        )

    assert exc_info.value.status_code == 404
