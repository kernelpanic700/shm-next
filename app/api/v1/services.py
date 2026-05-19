# =============================================================================
# shm-next — API v1: Services
# =============================================================================
"""Эндпоинты для управления услугами абонентов."""

from __future__ import annotations

from uuid import UUID

from litestar import Controller, delete, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from app.api.dependencies import get_service_service, provide_uow_dependency
from app.api.dto.requests import ServiceCreateRequest
from app.api.dto.responses import ServiceListResponse, ServiceResponse
from app.core.application.services.service_service import ServiceService
from app.infrastructure.db.unit_of_work import UnitOfWork


class ServiceController(Controller):
    """Контроллер для управления услугами абонентов."""

    path = "/v1/services"
    tags = ["Services"]

    dependencies = {
        "uow": Provide(provide_uow_dependency),
        "service_service": Provide(get_service_service),
    }

    @get("/", summary="Список услуг абонента")
    async def list_services(
        self,
        abonent_id: UUID,
        service_service: ServiceService,
        active_only: bool = True,
    ) -> ServiceListResponse:
        """Получить список услуг абонента."""
        services = await service_service.get_services(abonent_id=abonent_id, active_only=active_only)
        return ServiceListResponse(
            items=[ServiceResponse.model_validate(s, from_attributes=True).model_dump() for s in services],
            total=len(services),
            page=1,
            per_page=len(services),
        )

    @get("/{service_id:uuid}", summary="Получить услугу по ID")
    async def get_service(
        self,
        service_id: UUID,
        service_service: ServiceService,
    ) -> ServiceResponse:
        """Получить услугу по ID."""
        service = await service_service.get_service(service_id)
        if not service:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Service not found")
        return ServiceResponse.model_validate(service, from_attributes=True)

    @post("/", summary="Создать услугу", status_code=HTTP_201_CREATED)
    async def create_service(
        self,
        data: ServiceCreateRequest,
        uow: UnitOfWork,
        service_service: ServiceService,
    ) -> ServiceResponse:
        """Создать новую услугу для абонента."""
        async with uow:
            service = await service_service.activate_service(
                abonent_id=data.abonent_id,
                service_type=data.service_type,
                tariff_service_id=data.tariff_service_id,
                metadata=data.metadata,
            )
            await uow.commit()
            return ServiceResponse.model_validate(service, from_attributes=True)

    @delete("/{service_id:uuid}", summary="Деактивировать услугу", status_code=HTTP_204_NO_CONTENT)
    async def delete_service(
        self,
        service_id: UUID,
        uow: UnitOfWork,
        service_service: ServiceService,
    ) -> None:
        """Деактивировать услугу абонента."""
        async with uow:
            result = await service_service.deactivate_service(service_id)
            if not result:
                raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Service not found")
            await uow.commit()
