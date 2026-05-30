# =============================================================================
# shm-next - API v1: SHM Catalog Services
# =============================================================================
from __future__ import annotations

from uuid import UUID

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from app.api.dependencies import get_service_service, provide_uow_dependency
from app.api.dto.requests import (
    CatalogServiceCreateRequest,
    CatalogServiceOrderRequest,
    CatalogServiceUpdateRequest,
)
from app.api.dto.responses import (
    CatalogServiceListResponse,
    CatalogServiceResponse,
    ServiceResponse,
)
from app.core.application.services.service_service import ServiceService
from app.core.domain.entities.catalog_service import CatalogService
from app.core.domain.value_objects import Money
from app.infrastructure.db.unit_of_work import UnitOfWork


class CatalogServiceController(Controller):
    """Контроллер каталожных SHM-услуг."""

    path = "/catalog-services"
    tags = ["SHM Catalog Services"]
    dependencies = {
        "uow": Provide(provide_uow_dependency),
        "service_service": Provide(get_service_service, sync_to_thread=False),
    }

    @get("/", summary="Список каталожных SHM-услуг")
    async def list_catalog_services(
        self,
        uow: UnitOfWork,
        category: str | None = None,
        orderable_only: bool = False,
        include_deleted: bool = False,
    ) -> CatalogServiceListResponse:
        if orderable_only:
            services = await uow.catalog_services.get_orderable()
            if category:
                services = [service for service in services if service.category == category]
        else:
            services = await uow.catalog_services.list(
                category=category,
                include_deleted=include_deleted,
            )
        return CatalogServiceListResponse(
            items=[CatalogServiceResponse.model_validate(service) for service in services],
            total=len(services),
        )

    @get("/{service_id:uuid}", summary="Получить каталожную SHM-услугу")
    async def get_catalog_service(
        self,
        service_id: UUID,
        uow: UnitOfWork,
    ) -> CatalogServiceResponse:
        service = await uow.catalog_services.get(service_id)
        if service is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Catalog service {service_id} not found",
            )
        return CatalogServiceResponse.model_validate(service)

    @post("/", summary="Создать каталожную SHM-услугу", status_code=HTTP_201_CREATED)
    async def create_catalog_service(
        self,
        data: CatalogServiceCreateRequest,
        uow: UnitOfWork,
    ) -> CatalogServiceResponse:
        service = CatalogService(
            name=data.name,
            cost=Money(data.cost, data.currency),
            period_cost=data.period_cost,
            category=data.category,
            children=data.children,
            next_service_id=data.next_service_id,
            legacy_service_id=data.legacy_service_id,
            allow_to_order=data.allow_to_order,
            max_count=data.max_count,
            question=data.question,
            pay_always=data.pay_always,
            no_discount=data.no_discount,
            description=data.description,
            pay_in_credit=data.pay_in_credit,
            config=data.config,
            is_composite=data.is_composite,
        )
        saved = await uow.catalog_services.save(service)
        await uow.commit()
        return CatalogServiceResponse.model_validate(saved)

    @patch("/{service_id:uuid}", summary="Обновить каталожную SHM-услугу")
    async def update_catalog_service(
        self,
        service_id: UUID,
        data: CatalogServiceUpdateRequest,
        uow: UnitOfWork,
    ) -> CatalogServiceResponse:
        existing = await uow.catalog_services.get(service_id)
        if existing is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Catalog service {service_id} not found",
            )

        service = CatalogService(
            id=existing.id,
            name=data.name if data.name is not None else existing.name,
            cost=Money(
                data.cost if data.cost is not None else existing.cost.amount,
                data.currency if data.currency is not None else existing.cost.currency.value,
            ),
            period_cost=data.period_cost if data.period_cost is not None else existing.period_cost,
            category=data.category if data.category is not None else existing.category,
            children=data.children if data.children is not None else existing.children,
            next_service_id=data.next_service_id if data.next_service_id is not None else existing.next_service_id,
            legacy_service_id=data.legacy_service_id if data.legacy_service_id is not None else existing.legacy_service_id,
            allow_to_order=data.allow_to_order if data.allow_to_order is not None else existing.allow_to_order,
            max_count=data.max_count if data.max_count is not None else existing.max_count,
            question=data.question if data.question is not None else existing.question,
            pay_always=data.pay_always if data.pay_always is not None else existing.pay_always,
            no_discount=data.no_discount if data.no_discount is not None else existing.no_discount,
            description=data.description if data.description is not None else existing.description,
            pay_in_credit=data.pay_in_credit if data.pay_in_credit is not None else existing.pay_in_credit,
            config=data.config if data.config is not None else existing.config,
            is_composite=data.is_composite if data.is_composite is not None else existing.is_composite,
            is_deleted=data.is_deleted if data.is_deleted is not None else existing.is_deleted,
            created_at=existing.created_at,
            version=existing.version + 1,
        )
        saved = await uow.catalog_services.save(service)
        await uow.commit()
        return CatalogServiceResponse.model_validate(saved)

    @delete("/{service_id:uuid}", summary="Удалить каталожную SHM-услугу", status_code=HTTP_204_NO_CONTENT)
    async def delete_catalog_service(
        self,
        service_id: UUID,
        uow: UnitOfWork,
    ) -> None:
        service = await uow.catalog_services.get(service_id)
        if service is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Catalog service {service_id} not found",
            )
        service.mark_deleted()
        await uow.catalog_services.save(service)
        await uow.commit()

    @post("/{service_id:uuid}/order", summary="Заказать SHM-услугу")
    async def order_catalog_service(
        self,
        service_id: UUID,
        data: CatalogServiceOrderRequest,
        uow: UnitOfWork,
        service_service: ServiceService,
    ) -> ServiceResponse:
        bonus = Money(data.bonus_balance, "RUB") if data.bonus_balance is not None else None
        service = await service_service.order_catalog_service(
            abonent_id=data.abonent_id,
            catalog_service_id=service_id,
            quantity=data.quantity,
            abonent_discount_percent=data.abonent_discount_percent,
            bonus_balance=bonus,
            metadata=data.metadata,
        )
        await uow.commit()
        return ServiceResponse(
            id=service.id,
            abonent_id=service.abonent_id,
            service_type=service.service_type,
            status=service.status.value,
            activated_at=service.activated_at,
            deactivated_at=service.deactivated_at,
            cost=service.cost,
            currency=service.currency,
        )
