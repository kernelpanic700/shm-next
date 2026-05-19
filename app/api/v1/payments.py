# =============================================================================
# shm-next — API v1: Payments
# =============================================================================
"""Эндпоинты для управления платежами."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from litestar import Controller, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_201_CREATED, HTTP_404_NOT_FOUND

from app.api.dependencies import get_payment_service, provide_uow_dependency
from app.api.dto.requests import PaymentCreate
from app.api.dto.responses import PaymentListResponse, PaymentResponse
from app.core.application.payments.payment_service import PaymentService
from app.infrastructure.db.unit_of_work import UnitOfWork


class PaymentController(Controller):
    """Контроллер для управления платежами."""

    path = "/v1/payments"
    tags = ["Payments"]

    dependencies = {
        "uow": Provide(provide_uow_dependency),
        "payment_service": Provide(get_payment_service),
    }

    @get("/", summary="Список платежей")
    async def list_payments(
        self,
        abonent_id: UUID,
        payment_service: PaymentService,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> PaymentListResponse:
        """Получить список платежей абонента."""
        payments = await payment_service.get_payments_by_abonent(
            abonent_id=abonent_id,
            from_date=from_date,
            to_date=to_date,
            limit=per_page,
        )
        return PaymentListResponse(
            items=payments,
            total=len(payments),
            page=page,
            per_page=per_page,
        )

    @get("/{payment_id:uuid}", summary="Получить платёж")
    async def get_payment(
        self,
        payment_id: UUID,
        payment_service: PaymentService,
    ) -> PaymentResponse:
        """Получить платёж по ID."""
        payment = await payment_service.get_payment(payment_id)
        if not payment:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Payment not found")
        return PaymentResponse.model_validate(payment, from_attributes=True)

    @post("/", summary="Создать платёж", status_code=HTTP_201_CREATED)
    async def create_payment(
        self,
        data: PaymentCreate,
        uow: UnitOfWork,
        payment_service: PaymentService,
    ) -> PaymentResponse:
        """Создать новый платёж."""
        async with uow:
            payment = await payment_service.create_payment(
                abonent_id=data.abonent_id,
                amount=data.amount,
                currency=data.currency,
            )
            await uow.commit()
            return PaymentResponse.model_validate(payment, from_attributes=True)

    @post("/{payment_id:uuid}/confirm", summary="Подтвердить платёж")
    async def confirm_payment(
        self,
        payment_id: UUID,
        uow: UnitOfWork,
        payment_service: PaymentService,
    ) -> PaymentResponse:
        """Подтвердить платёж."""
        async with uow:
            result = await payment_service.confirm_payment(payment_id)
            if not result:
                raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Payment not found")
            payment = await payment_service.get_payment(payment_id)
            await uow.commit()
            return PaymentResponse.model_validate(payment, from_attributes=True)

    @post("/{payment_id:uuid}/refund", summary="Возврат платежа")
    async def refund_payment(
        self,
        payment_id: UUID,
        uow: UnitOfWork,
        payment_service: PaymentService,
    ) -> PaymentResponse:
        """Выполнить возврат платежа."""
        async with uow:
            result = await payment_service.refund_payment(payment_id)
            if not result:
                raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Payment not found")
            payment = await payment_service.get_payment(payment_id)
            await uow.commit()
            return PaymentResponse.model_validate(payment, from_attributes=True)
