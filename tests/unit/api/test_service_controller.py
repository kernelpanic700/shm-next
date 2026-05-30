from decimal import Decimal
from uuid import uuid4

import pytest
from litestar.exceptions import HTTPException

from app.api.dto.requests import ServiceCreateRequest, ServiceRenewRequest, ServiceStopRequest
from app.api.v1.services import ServiceController
from app.core.domain.entities import UserService
from app.core.domain.value_objects import ServiceStatus


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commit_count = 0

    async def commit(self) -> None:
        self.commit_count += 1


class FakeServiceService:
    def __init__(self) -> None:
        self.activate_calls: list[dict] = []
        self.deactivate_calls: list[dict] = []
        self.renew_calls: list[dict] = []
        self.stop_calls: list[dict] = []
        self.service = UserService(
            abonent_id=uuid4(),
            service_type="internet",
            catalog_service_id=uuid4(),
            status=ServiceStatus.ACTIVE,
            cost=500.0,
            currency="RUB",
        )
        self.services = [self.service]

    async def activate_service(self, **kwargs) -> UserService:
        self.activate_calls.append(kwargs)
        self.service = UserService(
            abonent_id=kwargs["abonent_id"],
            service_type=kwargs["service_type"],
            tariff_service_id=kwargs["tariff_service_id"],
            metadata=kwargs["metadata"],
            status=ServiceStatus.ACTIVE,
            cost=0,
            currency="RUB",
        )
        self.services = [self.service]
        return self.service

    async def deactivate_service(self, **kwargs) -> UserService:
        self.deactivate_calls.append(kwargs)
        self.service.deactivate(reason=kwargs["reason"])
        return self.service

    async def get_service(self, service_id):
        return self.service if service_id == self.service.id else None

    async def get_services(self, **kwargs) -> list[UserService]:
        return self.services

    async def renew_catalog_service(self, **kwargs) -> UserService:
        self.renew_calls.append(kwargs)
        return self.service

    async def stop_catalog_service(self, **kwargs) -> UserService:
        self.stop_calls.append(kwargs)
        self.service.deactivate(reason=kwargs["reason"])
        return self.service


@pytest.mark.asyncio
async def test_list_services_uses_application_service() -> None:
    service_service = FakeServiceService()

    response = await ServiceController.list_services.fn(
        None,
        abonent_id=service_service.service.abonent_id,
        active_only=True,
        service_service=service_service,
    )

    assert response.total == 1
    assert response.items[0].id == service_service.service.id
    assert response.items[0].catalog_service_id == service_service.service.catalog_service_id
    assert response.items[0].period_cost == "1.0000"


@pytest.mark.asyncio
async def test_get_service_returns_404_for_other_abonent() -> None:
    service_service = FakeServiceService()

    with pytest.raises(HTTPException) as exc_info:
        await ServiceController.get_service.fn(
            None,
            abonent_id=uuid4(),
            service_id=service_service.service.id,
            service_service=service_service,
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_service_activates_and_commits() -> None:
    uow = FakeUnitOfWork()
    service_service = FakeServiceService()
    abonent_id = uuid4()
    request = ServiceCreateRequest(
        abonent_id=abonent_id,
        service_type="static_ip",
        metadata={"ip": "10.0.0.1"},
    )

    response = await ServiceController.create_service.fn(
        None,
        abonent_id=abonent_id,
        data=request,
        uow=uow,
        service_service=service_service,
    )

    assert uow.commit_count == 1
    assert service_service.activate_calls == [
        {
            "abonent_id": abonent_id,
            "service_type": "static_ip",
            "tariff_service_id": None,
            "metadata": {"ip": "10.0.0.1"},
        }
    ]
    assert response.status == "ACTIVE"
    assert response.service_type == "static_ip"


@pytest.mark.asyncio
async def test_renew_shm_service_commits_unit_of_work() -> None:
    uow = FakeUnitOfWork()
    service_service = FakeServiceService()
    service_id = uuid4()
    request = ServiceRenewRequest(
        abonent_discount_percent=15,
        bonus_balance=Decimal("20.00"),
    )

    response = await ServiceController.renew_shm_service.fn(
        None,
        service_id=service_id,
        data=request,
        uow=uow,
        service_service=service_service,
    )

    assert uow.commit_count == 1
    assert len(service_service.renew_calls) == 1
    assert service_service.renew_calls[0]["service_id"] == service_id
    assert service_service.renew_calls[0]["abonent_discount_percent"] == 15
    assert service_service.renew_calls[0]["bonus_balance"].amount == Decimal("20.00")
    assert response.id == service_service.service.id
    assert response.status == "ACTIVE"


@pytest.mark.asyncio
async def test_stop_shm_service_commits_unit_of_work() -> None:
    uow = FakeUnitOfWork()
    service_service = FakeServiceService()
    service_id = uuid4()
    request = ServiceStopRequest(reason="user_request")

    response = await ServiceController.stop_shm_service.fn(
        None,
        service_id=service_id,
        data=request,
        uow=uow,
        service_service=service_service,
    )

    assert uow.commit_count == 1
    assert service_service.stop_calls == [
        {
            "service_id": service_id,
            "reason": "user_request",
        }
    ]
    assert response.id == service_service.service.id
    assert response.status == "DEACTIVATED"


@pytest.mark.asyncio
async def test_delete_service_deactivates_matching_service() -> None:
    uow = FakeUnitOfWork()
    service_service = FakeServiceService()

    await ServiceController.delete_service.fn(
        None,
        abonent_id=service_service.service.abonent_id,
        service_id=service_service.service.id,
        uow=uow,
        service_service=service_service,
    )

    assert uow.commit_count == 1
    assert service_service.deactivate_calls == [
        {
            "service_id": service_service.service.id,
            "reason": "api_delete",
        }
    ]
