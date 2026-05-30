from uuid import uuid4

import pytest
from litestar.exceptions import HTTPException

from app.api.dto.requests import TariffCreateRequest, TariffUpdateRequest
from app.api.v1.tariffs import TariffController
from app.core.domain.entities.tariff import Tariff


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commit_count = 0

    async def commit(self) -> None:
        self.commit_count += 1


class FakeTariffService:
    def __init__(self) -> None:
        self.tariff = Tariff(
            name="Base",
            description="Base tariff",
            services=[{"service_type": "internet"}],
            price=500,
            currency="RUB",
            billing_period="monthly",
        )
        self.create_calls: list[TariffCreateRequest] = []
        self.update_calls: list[tuple] = []
        self.deactivate_calls: list = []

    async def list_tariffs(self, active_only: bool = True) -> list[Tariff]:
        return [self.tariff] if active_only else [self.tariff, Tariff(name="Archive", is_active=False)]

    async def get_tariff(self, tariff_id):
        return self.tariff if tariff_id == self.tariff.id else None

    async def get_tariff_by_name(self, name: str):
        return self.tariff if name == self.tariff.name else None

    async def create_tariff(self, data: TariffCreateRequest) -> Tariff:
        self.create_calls.append(data)
        self.tariff = Tariff(
            name=data.name,
            description=data.description or "",
            services=data.services,
            is_active=data.is_active,
            price=data.price,
            currency=data.currency,
            billing_period=data.billing_period,
        )
        return self.tariff

    async def update_tariff(self, tariff_id, data: TariffUpdateRequest) -> Tariff:
        self.update_calls.append((tariff_id, data))
        if tariff_id != self.tariff.id:
            raise ValueError(f"Tariff {tariff_id} not found")
        if data.name is not None:
            self.tariff.name = data.name
        if data.price is not None:
            self.tariff.price = data.price
        return self.tariff

    async def deactivate_tariff(self, tariff_id) -> None:
        self.deactivate_calls.append(tariff_id)
        if tariff_id != self.tariff.id:
            raise ValueError(f"Tariff {tariff_id} not found")
        self.tariff.is_active = False


@pytest.mark.asyncio
async def test_list_tariffs_returns_real_tariff_list() -> None:
    tariff_service = FakeTariffService()

    response = await TariffController.list_tariffs.fn(
        None,
        active_only=True,
        tariff_service=tariff_service,
    )

    assert response.total == 1
    assert response.items[0].id == tariff_service.tariff.id
    assert response.items[0].price == 500


@pytest.mark.asyncio
async def test_get_tariff_returns_404_when_missing() -> None:
    tariff_service = FakeTariffService()

    with pytest.raises(HTTPException) as exc_info:
        await TariffController.get_tariff.fn(
            None,
            tariff_id=uuid4(),
            tariff_service=tariff_service,
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_tariff_commits_unit_of_work() -> None:
    uow = FakeUnitOfWork()
    tariff_service = FakeTariffService()
    request = TariffCreateRequest(
        name="Premium",
        description="Premium tariff",
        services=[],
        price=1200,
        currency="RUB",
        billing_period="monthly",
    )

    response = await TariffController.create_tariff.fn(
        None,
        data=request,
        uow=uow,
        tariff_service=tariff_service,
    )

    assert uow.commit_count == 1
    assert tariff_service.create_calls == [request]
    assert response.name == "Premium"
    assert response.price == 1200


@pytest.mark.asyncio
async def test_update_tariff_commits_unit_of_work() -> None:
    uow = FakeUnitOfWork()
    tariff_service = FakeTariffService()
    request = TariffUpdateRequest(name="Updated", price=900)

    response = await TariffController.update_tariff.fn(
        None,
        tariff_id=tariff_service.tariff.id,
        data=request,
        uow=uow,
        tariff_service=tariff_service,
    )

    assert uow.commit_count == 1
    assert response.name == "Updated"
    assert response.price == 900


@pytest.mark.asyncio
async def test_deactivate_tariff_commits_unit_of_work() -> None:
    uow = FakeUnitOfWork()
    tariff_service = FakeTariffService()

    await TariffController.deactivate_tariff.fn(
        None,
        tariff_id=tariff_service.tariff.id,
        uow=uow,
        tariff_service=tariff_service,
    )

    assert uow.commit_count == 1
    assert tariff_service.tariff.is_active is False
