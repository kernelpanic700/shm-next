from decimal import Decimal
from uuid import uuid4

import pytest
from litestar.exceptions import HTTPException

from app.api.dto.requests import (
    AbonentCreateRequest,
    AbonentUpdateRequest,
    BalanceTopUpRequest,
)
from app.api.v1.abonents import AbonentController
from app.core.domain.entities.abonent import Abonent, AbonentCreate, AbonentUpdate
from app.core.domain.value_objects import Money


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
        self.close_count += 1

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1


class FakeAbonentService:
    def __init__(self) -> None:
        self.abonent = Abonent(
            full_name="Test User",
            phone="+79990000001",
            account_number="ACC001",
            balance=Money(100, "RUB"),
        )
        self.create_calls: list[AbonentCreate] = []
        self.update_calls: list[tuple] = []
        self.deactivate_calls: list = []
        self.balance_calls: list[tuple] = []

    async def list_abonents(self, **kwargs):
        return [self.abonent]

    async def get_abonent(self, abonent_id):
        return self.abonent if abonent_id == self.abonent.id else None

    async def get_abonent_by_phone(self, phone: str):
        return self.abonent if phone == self.abonent.phone else None

    async def get_abonent_by_account(self, account_number: str):
        return self.abonent if account_number == self.abonent.account_number else None

    async def create_abonent(self, data: AbonentCreate):
        self.create_calls.append(data)
        if data.phone == "+79990000999":
            raise ValueError("Abonent with phone already exists")
        self.abonent = Abonent(
            full_name=data.full_name,
            phone=data.phone,
            account_number=data.account_number,
            balance=Money(data.balance, data.currency),
            allow_negative=data.allow_negative,
            tariff_id=data.tariff_id,
        )
        return self.abonent

    async def update_abonent(self, abonent_id, data: AbonentUpdate):
        self.update_calls.append((abonent_id, data))
        if abonent_id != self.abonent.id:
            return None
        if data.phone == "+79990000999":
            raise ValueError("Phone already belongs to another abonent")
        if data.full_name is not None:
            self.abonent._full_name = data.full_name
        return self.abonent

    async def deactivate_abonent(self, abonent_id):
        self.deactivate_calls.append(abonent_id)
        if abonent_id != self.abonent.id:
            return None
        self.abonent._status = self.abonent.status.INACTIVE
        return self.abonent

    async def change_balance(self, abonent_id, amount: float, currency: str, reason: str):
        self.balance_calls.append((abonent_id, amount, currency, reason))
        if abonent_id != self.abonent.id:
            raise ValueError(f"Abonent {abonent_id} not found")
        self.abonent.change_balance(Money(amount, currency), reason=reason)
        return self.abonent


@pytest.mark.asyncio
async def test_list_abonents_uses_application_service() -> None:
    abonent_service = FakeAbonentService()

    response = await AbonentController.list_abonents.fn(
        None,
        abonent_service=abonent_service,
        page=1,
        size=20,
        status=None,
        tariff_id=None,
        min_balance=None,
        max_balance=None,
    )

    assert response.total == 1
    assert response.items[0].id == abonent_service.abonent.id


@pytest.mark.asyncio
async def test_get_abonent_returns_404_when_missing() -> None:
    abonent_service = FakeAbonentService()

    with pytest.raises(HTTPException) as exc_info:
        await AbonentController.get_abonent.fn(
            None,
            abonent_id=uuid4(),
            abonent_service=abonent_service,
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_abonent_commits_unit_of_work() -> None:
    uow = FakeUnitOfWork()
    abonent_service = FakeAbonentService()
    request = AbonentCreateRequest(
        full_name="New User",
        phone="+79990000002",
        account_number="ACC002",
        balance=250,
    )

    response = await AbonentController.create_abonent.fn(
        None,
        data=request,
        uow=uow,
        abonent_service=abonent_service,
    )

    assert response.full_name == "New User"
    assert abonent_service.create_calls[0].phone == "+79990000002"
    assert uow.commit_count == 2


@pytest.mark.asyncio
async def test_create_abonent_returns_409_for_duplicate() -> None:
    uow = FakeUnitOfWork()
    abonent_service = FakeAbonentService()
    request = AbonentCreateRequest(
        full_name="Dup User",
        phone="+79990000999",
        account_number="ACC999",
    )

    with pytest.raises(HTTPException) as exc_info:
        await AbonentController.create_abonent.fn(
            None,
            data=request,
            uow=uow,
            abonent_service=abonent_service,
        )

    assert exc_info.value.status_code == 409
    assert uow.rollback_count == 1


@pytest.mark.asyncio
async def test_update_abonent_commits_unit_of_work() -> None:
    uow = FakeUnitOfWork()
    abonent_service = FakeAbonentService()
    request = AbonentUpdateRequest(full_name="Updated User")

    response = await AbonentController.update_abonent.fn(
        None,
        abonent_id=abonent_service.abonent.id,
        data=request,
        uow=uow,
        abonent_service=abonent_service,
    )

    assert response.full_name == "Updated User"
    assert uow.commit_count == 2


@pytest.mark.asyncio
async def test_delete_abonent_deactivates_via_service() -> None:
    uow = FakeUnitOfWork()
    abonent_service = FakeAbonentService()

    await AbonentController.delete_abonent.fn(
        None,
        abonent_id=abonent_service.abonent.id,
        uow=uow,
        abonent_service=abonent_service,
    )

    assert abonent_service.deactivate_calls == [abonent_service.abonent.id]
    assert abonent_service.abonent.status.value == "INACTIVE"
    assert uow.commit_count == 2


@pytest.mark.asyncio
async def test_top_up_balance_uses_application_service() -> None:
    uow = FakeUnitOfWork()
    abonent_service = FakeAbonentService()
    request = BalanceTopUpRequest(amount=Decimal("150.00"), payment_method="manual")

    response = await AbonentController.top_up_balance.fn(
        None,
        abonent_id=abonent_service.abonent.id,
        data=request,
        uow=uow,
        abonent_service=abonent_service,
    )

    assert response.balance == 250
    assert abonent_service.balance_calls[0][1] == 150
    assert uow.commit_count == 2
