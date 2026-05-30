# =============================================================================
# shm-next — API v1: Invoices
# =============================================================================
"""Эндпоинты для работы со счетами."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from litestar import Controller, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter

from app.api.dependencies import get_invoice_service, provide_uow_dependency
from app.api.dto.requests import InvoiceCreateRequest
from app.api.dto.responses import ApiResponse, InvoiceResponse
from app.core.application.invoices.invoice_service import (
    InvoiceCreateCommand,
    InvoiceService,
)
from app.infrastructure.db.unit_of_work import UnitOfWork


class InvoiceController(Controller):
    path = "/invoices"
    tags = ["Invoices"]
    dependencies = {
        "uow": Provide(provide_uow_dependency),
        "invoice_service": Provide(get_invoice_service, sync_to_thread=False),
    }

    @get(
        "/",
        summary="Список счетов",
        description="Получить список счетов абонента",
    )
    async def list_invoices(
        self,
        invoice_service: InvoiceService,
        abonent_id: UUID | None = Parameter(query="abonent_id", required=False),
        status: str | None = Parameter(query="status", required=False),
        from_date: datetime | None = Parameter(query="from_date", required=False),
        to_date: datetime | None = Parameter(query="to_date", required=False),
        page: int = 1,
        per_page: int = 50,
    ) -> ApiResponse:
        offset = (page - 1) * per_page
        invoices, total = await invoice_service.list_invoices(
            abonent_id=abonent_id,
            status=status,
            from_date=from_date,
            to_date=to_date,
            offset=offset,
            limit=per_page,
        )
        return ApiResponse(
            success=True,
            data={
                "items": [
                    InvoiceResponse.model_validate(invoice, from_attributes=True).model_dump(
                        mode="json"
                    )
                    for invoice in invoices
                ],
                "total": total,
                "page": page,
                "per_page": per_page,
            },
        )

    @post(
        "/",
        summary="Создать счёт",
        description="Создать счёт абоненту",
    )
    async def create_invoice(
        self,
        data: InvoiceCreateRequest,
        uow: UnitOfWork,
        invoice_service: InvoiceService,
    ) -> InvoiceResponse:
        try:
            saved = await invoice_service.create_invoice(
                InvoiceCreateCommand(
                    abonent_id=data.abonent_id,
                    amount=data.amount,
                    currency=data.currency,
                    period_start=data.period_start,
                    period_end=data.period_end,
                    due_date=data.due_date,
                    description=data.description,
                    metadata=data.metadata,
                    issue_now=data.issue_now,
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        await uow.commit()
        return InvoiceResponse.model_validate(saved)

    @get(
        "/{invoice_id:uuid}",
        summary="Получить счёт",
        description="Получить данные счёта по ID",
    )
    async def get_invoice(
        self,
        invoice_id: UUID,
        invoice_service: InvoiceService,
    ) -> ApiResponse:
        invoice = await invoice_service.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return ApiResponse(
            success=True,
            data=InvoiceResponse.model_validate(invoice, from_attributes=True).model_dump(
                mode="json"
            ),
        )

    @post("/{invoice_id:uuid}/issue", summary="Выставить счёт")
    async def issue_invoice(
        self,
        invoice_id: UUID,
        uow: UnitOfWork,
        invoice_service: InvoiceService,
    ) -> InvoiceResponse:
        saved = await _run_invoice_action(invoice_service.issue_invoice, invoice_id)
        await uow.commit()
        return InvoiceResponse.model_validate(saved)

    @post("/{invoice_id:uuid}/send", summary="Отметить счёт отправленным")
    async def send_invoice(
        self,
        invoice_id: UUID,
        uow: UnitOfWork,
        invoice_service: InvoiceService,
    ) -> InvoiceResponse:
        saved = await _run_invoice_action(invoice_service.send_invoice, invoice_id)
        await uow.commit()
        return InvoiceResponse.model_validate(saved)

    @post("/{invoice_id:uuid}/overdue", summary="Отметить счёт просроченным")
    async def mark_invoice_overdue(
        self,
        invoice_id: UUID,
        uow: UnitOfWork,
        invoice_service: InvoiceService,
    ) -> InvoiceResponse:
        saved = await _run_invoice_action(invoice_service.mark_overdue, invoice_id)
        await uow.commit()
        return InvoiceResponse.model_validate(saved)

    @post("/{invoice_id:uuid}/cancel", summary="Отменить счёт")
    async def cancel_invoice(
        self,
        invoice_id: UUID,
        uow: UnitOfWork,
        invoice_service: InvoiceService,
    ) -> InvoiceResponse:
        saved = await _run_invoice_action(invoice_service.cancel_invoice, invoice_id)
        await uow.commit()
        return InvoiceResponse.model_validate(saved)

    @post(
        "/{invoice_id:uuid}/pay",
        summary="Оплата счёта",
        description="Оплатить счёт по ID",
    )
    async def pay_invoice(
        self,
        invoice_id: UUID,
        uow: UnitOfWork,
        invoice_service: InvoiceService,
        payment_method: str = Parameter(query="payment_method", default="manual"),
        external_id: str | None = Parameter(query="external_id", required=False),
    ) -> ApiResponse:
        try:
            result = await invoice_service.pay_invoice(
                invoice_id=invoice_id,
                payment_method=payment_method,
                external_id=external_id,
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        await uow.commit()

        return ApiResponse(
            success=True,
            data={
                "paid": True,
                "payment_id": str(result.payment_id),
            },
        )


async def _run_invoice_action(action, invoice_id: UUID):
    try:
        return await action(invoice_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
