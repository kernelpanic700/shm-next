from decimal import Decimal
from uuid import uuid4

import pytest

from app.api.dto.requests import CatalogServiceOrderRequest
from app.api.v1.catalog_services import CatalogServiceController
from app.core.domain.entities import UserService
from app.core.domain.value_objects import ServiceStatus


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commit_count = 0

    async def commit(self) -> None:
        self.commit_count += 1


class FakeServiceService:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.service = UserService(
            abonent_id=uuid4(),
            service_type="internet",
            catalog_service_id=uuid4(),
            status=ServiceStatus.ACTIVE,
            cost=450.0,
            currency="RUB",
        )

    async def order_catalog_service(self, **kwargs) -> UserService:
        self.calls.append(kwargs)
        return self.service


@pytest.mark.asyncio
async def test_order_catalog_service_commits_unit_of_work() -> None:
    uow = FakeUnitOfWork()
    service_service = FakeServiceService()
    catalog_service_id = uuid4()
    abonent_id = uuid4()
    request = CatalogServiceOrderRequest(
        abonent_id=abonent_id,
        quantity=2,
        abonent_discount_percent=10,
        bonus_balance=Decimal("25.00"),
        metadata={"source": "api-test"},
    )

    response = await CatalogServiceController.order_catalog_service.fn(
        None,
        service_id=catalog_service_id,
        data=request,
        uow=uow,
        service_service=service_service,
    )

    assert uow.commit_count == 1
    assert len(service_service.calls) == 1
    assert service_service.calls[0]["abonent_id"] == abonent_id
    assert service_service.calls[0]["catalog_service_id"] == catalog_service_id
    assert service_service.calls[0]["quantity"] == 2
    assert service_service.calls[0]["abonent_discount_percent"] == 10
    assert service_service.calls[0]["bonus_balance"].amount == Decimal("25.00")
    assert service_service.calls[0]["metadata"] == {"source": "api-test"}
    assert response.id == service_service.service.id
    assert response.status == "ACTIVE"
    assert response.cost == 450.0
