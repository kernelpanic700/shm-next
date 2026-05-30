# =============================================================================
# shm-next — API v1: Services
# =============================================================================
"""
Эндпоинты для управления услугами абонентов.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from litestar import Controller, delete, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from app.api.dependencies import get_service_service, provide_uow_dependency
from app.api.dto.requests import ServiceCreateRequest, ServiceRenewRequest, ServiceStopRequest
from app.api.dto.responses import ServiceListResponse, ServiceResponse
from app.core.application.services.service_service import ServiceService
from app.core.domain.entities.service import UserService
from app.core.domain.value_objects import Money
from app.infrastructure.db.unit_of_work import UnitOfWork


def _to_service_response(service: UserService) -> ServiceResponse:
    return ServiceResponse(
        id=service.id,
        abonent_id=service.abonent_id,
        service_type=service.service_type,
        tariff_service_id=service.tariff_service_id,
        catalog_service_id=service.catalog_service_id,
        status=service.status.value,
        activated_at=service.activated_at,
        deactivated_at=service.deactivated_at,
        expire_at=service.expire_at,
        cost=service.cost,
        currency=service.currency,
        period_cost=str(service.period_cost),
        next_service_id=service.next_service_id,
        parent_id=service.parent_id,
        quantity=service.quantity,
        auto_bill=service.auto_bill,
        pay_always=service.pay_always,
        pay_in_credit=service.pay_in_credit,
        no_discount=service.no_discount,
        metadata=service.metadata,
    )


class ServiceController(Controller):
    """Контроллер для управления услугами абонентов."""

    path = "/services"
    tags = ["Services"]
    dependencies = {
        "uow": Provide(provide_uow_dependency),
        "service_service": Provide(get_service_service, sync_to_thread=False),
    }

    # --- Demo endpoints (string ID support) ---

    @get("/demo/{abonent_id:str}/", summary="Список услуг абонента (demo)")
    async def list_services_demo(
        self,
        abonent_id: str,
        active_only: bool = True,
    ) -> dict:
        """Получить список услуг абонента (demo mode)."""
        mock_services = [
            {"id": "svc-1", "name": "Интернет", "type": "internet", "status": "active", "price": 300.0},
            {"id": "svc-2", "name": "Телефония", "type": "voice", "status": "active", "price": 200.0},
        ]
        return {"items": mock_services, "total": len(mock_services), "page": 1, "per_page": len(mock_services)}

    # --- UUID endpoints ---

    @get("/{abonent_id:uuid}/", summary="Список услуг абонента")
    async def list_services(
        self,
        abonent_id: UUID,
        service_service: ServiceService,
        active_only: bool = True,
    ) -> ServiceListResponse:
        """Получить список услуг абонента."""
        services = await service_service.get_services(
            abonent_id=abonent_id,
            active_only=active_only,
        )
        items = [_to_service_response(service) for service in services]
        return ServiceListResponse(
            items=items,
            total=len(items),
            page=1,
            per_page=len(items),
        )

    @get("/{abonent_id:uuid}/{service_id:uuid}", summary="Получить услугу по ID")
    async def get_service(
        self,
        abonent_id: UUID,
        service_id: UUID,
        service_service: ServiceService,
    ) -> ServiceResponse:
        """Получить услугу по ID."""
        service = await service_service.get_service(service_id)
        if service is None or service.abonent_id != abonent_id:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Service {service_id} not found",
            )
        return _to_service_response(service)

    @post("/{abonent_id:uuid}/", summary="Создать услугу", status_code=HTTP_201_CREATED)
    async def create_service(
        self,
        abonent_id: UUID,
        data: ServiceCreateRequest,
        uow: UnitOfWork,
        service_service: ServiceService,
    ) -> ServiceResponse:
        """Создать новую услугу для абонента."""
        if data.abonent_id != abonent_id:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Abonent {data.abonent_id} does not match route abonent",
            )
        service = await service_service.activate_service(
            abonent_id=abonent_id,
            service_type=data.service_type,
            tariff_service_id=data.tariff_service_id,
            metadata=data.metadata,
        )
        await uow.commit()
        return _to_service_response(service)

    @post("/{service_id:uuid}/renew", summary="Продлить SHM-услугу")
    async def renew_shm_service(
        self,
        service_id: UUID,
        data: ServiceRenewRequest,
        uow: UnitOfWork,
        service_service: ServiceService,
    ) -> ServiceResponse:
        """Продлить SHM-услугу абонента."""
        bonus = Money(data.bonus_balance, "RUB") if data.bonus_balance is not None else None
        service = await service_service.renew_catalog_service(
            service_id=service_id,
            abonent_discount_percent=data.abonent_discount_percent,
            bonus_balance=bonus,
        )
        await uow.commit()
        return _to_service_response(service)

    @post("/{service_id:uuid}/stop", summary="Остановить SHM-услугу")
    async def stop_shm_service(
        self,
        service_id: UUID,
        data: ServiceStopRequest,
        uow: UnitOfWork,
        service_service: ServiceService,
    ) -> ServiceResponse:
        """Остановить SHM-услугу и вернуть неиспользованный остаток периода."""
        service = await service_service.stop_catalog_service(
            service_id=service_id,
            reason=data.reason,
        )
        await uow.commit()
        return _to_service_response(service)

    @delete("/{abonent_id:uuid}/{service_id:uuid}", summary="Деактивировать услугу", status_code=HTTP_204_NO_CONTENT)
    async def delete_service(
        self,
        abonent_id: UUID,
        service_id: UUID,
        uow: UnitOfWork,
        service_service: ServiceService,
    ) -> None:
        """Деактивировать услугу абонента."""
        service = await service_service.get_service(service_id)
        if service is None or service.abonent_id != abonent_id:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Service {service_id} not found",
            )
        await service_service.deactivate_service(
            service_id=service_id,
            reason="api_delete",
        )
        await uow.commit()
