# =============================================================================
# shm-next - API v1: Discounts
# =============================================================================
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from litestar import Controller, get, patch, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_201_CREATED, HTTP_404_NOT_FOUND

from app.api.dependencies import provide_uow_dependency
from app.api.dto.requests import DiscountCreateRequest, DiscountUpdateRequest
from app.api.dto.responses import DiscountListResponse, DiscountResponse
from app.core.domain.entities.discount import Discount
from app.infrastructure.db.unit_of_work import UnitOfWork


class DiscountController(Controller):
    """Контроллер скидок."""

    path = "/discounts"
    tags = ["Discounts"]
    dependencies = {"uow": Provide(provide_uow_dependency)}

    @get("/", summary="Список скидок")
    async def list_discounts(
        self,
        uow: UnitOfWork,
        active_only: bool = False,
        valid_now: bool = False,
    ) -> DiscountListResponse:
        if valid_now:
            discounts = await uow.discounts.get_valid_at(datetime.now(UTC))
        elif active_only:
            discounts = await uow.discounts.get_active()
        else:
            discounts = await uow.discounts.get_active()

        return DiscountListResponse(
            items=[DiscountResponse.model_validate(discount) for discount in discounts],
            total=len(discounts),
        )

    @get("/{discount_id:uuid}", summary="Получить скидку")
    async def get_discount(
        self,
        discount_id: UUID,
        uow: UnitOfWork,
    ) -> DiscountResponse:
        discount = await uow.discounts.get(discount_id)
        if discount is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Discount {discount_id} not found",
            )
        return DiscountResponse.model_validate(discount)

    @post("/", summary="Создать скидку", status_code=HTTP_201_CREATED)
    async def create_discount(
        self,
        data: DiscountCreateRequest,
        uow: UnitOfWork,
    ) -> DiscountResponse:
        discount = Discount(
            name=data.name,
            description=data.description,
            discount_type=data.discount_type,
            value=float(data.value),
            currency=data.currency,
            valid_from=data.valid_from,
            valid_to=data.valid_to,
            is_active=data.is_active,
            max_uses=data.max_uses,
        )
        saved = await uow.discounts.save(discount)
        await uow.commit()
        return DiscountResponse.model_validate(saved)

    @patch("/{discount_id:uuid}", summary="Обновить скидку")
    async def update_discount(
        self,
        discount_id: UUID,
        data: DiscountUpdateRequest,
        uow: UnitOfWork,
    ) -> DiscountResponse:
        existing = await uow.discounts.get(discount_id)
        if existing is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Discount {discount_id} not found",
            )

        discount = Discount(
            id=existing.id,
            name=data.name if data.name is not None else existing.name,
            description=data.description
            if data.description is not None
            else existing.description,
            discount_type=data.discount_type
            if data.discount_type is not None
            else existing.discount_type,
            value=float(data.value) if data.value is not None else existing.value,
            currency=data.currency if data.currency is not None else existing.currency,
            valid_from=data.valid_from
            if data.valid_from is not None
            else existing.valid_from,
            valid_to=data.valid_to if data.valid_to is not None else existing.valid_to,
            is_active=data.is_active
            if data.is_active is not None
            else existing.is_active,
            max_uses=data.max_uses
            if data.max_uses is not None
            else existing.max_uses,
            used_count=existing.used_count,
            created_at=existing.created_at,
            version=existing.version + 1,
        )
        saved = await uow.discounts.save(discount)
        await uow.commit()
        return DiscountResponse.model_validate(saved)

    @post("/{discount_id:uuid}/deactivate", summary="Деактивировать скидку")
    async def deactivate_discount(
        self,
        discount_id: UUID,
        uow: UnitOfWork,
    ) -> DiscountResponse:
        discount = await uow.discounts.get(discount_id)
        if discount is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Discount {discount_id} not found",
            )

        discount.deactivate()
        saved = await uow.discounts.save(discount)
        await uow.commit()
        return DiscountResponse.model_validate(saved)
