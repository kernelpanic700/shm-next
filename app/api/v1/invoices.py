# =============================================================================
# shm-next — API v1: Invoices
# =============================================================================
"""Эндпоинты для работы со счетами."""

from __future__ import annotations

from uuid import UUID

from litestar import Controller, get, post
from litestar.datastructures import State
from litestar.exceptions import HTTPException

from app.api.dto.responses import ApiResponse


class InvoiceController(Controller):
    path = "/v1/invoices"
    tags = ["Invoices"]

    @get(
        "/",
        summary="Список счетов",
        description="Получить список счетов абонента",
    )
    async def list_invoices(
        self,
        abonent_id: UUID,
        state: State,
        status: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> ApiResponse:
        from sqlalchemy import select

        from app.infrastructure.db.models import Invoice

        session = state.session
        stmt = select(Invoice).where(Invoice.abonent_id == abonent_id)

        if status:
            stmt = stmt.where(Invoice.status == status)

        stmt = stmt.order_by(Invoice.created_at.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page)

        result = await session.execute(stmt)
        invoices = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                "items": [
                    {
                        "id": str(inv.id),
                        "abonent_id": str(inv.abonent_id),
                        "amount": inv.amount,
                        "currency": inv.currency,
                        "status": inv.status,
                        "period_start": inv.period_start.isoformat() if inv.period_start else None,
                        "period_end": inv.period_end.isoformat() if inv.period_end else None,
                        "created_at": inv.created_at.isoformat() if inv.created_at else None,
                        "due_date": inv.due_date.isoformat() if inv.due_date else None,
                    }
                    for inv in invoices
                ],
                "total": len(invoices),
                "page": page,
                "per_page": per_page,
            },
        )

    @get(
        "/{invoice_id:uuid}",
        summary="Получить счёт",
        description="Получить данные счёта по ID",
    )
    async def get_invoice(
        self,
        invoice_id: UUID,
        state: State,
    ) -> ApiResponse:
        from app.infrastructure.db.models import Invoice

        invoice = await state.session.get(Invoice, invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return ApiResponse(
            success=True,
            data={
                "id": str(invoice.id),
                "abonent_id": str(invoice.abonent_id),
                "amount": invoice.amount,
                "currency": invoice.currency,
                "status": invoice.status,
                "period_start": invoice.period_start.isoformat() if invoice.period_start else None,
                "period_end": invoice.period_end.isoformat() if invoice.period_end else None,
                "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
            },
        )

    @post(
        "/{invoice_id:uuid}/pay",
        summary="Оплата счёта",
        description="Оплатить счёт по ID",
    )
    async def pay_invoice(
        self,
        invoice_id: UUID,
        state: State,
    ) -> ApiResponse:
        from app.core.domain.value_objects import InvoiceStatus
        from app.infrastructure.db.models import Invoice

        invoice = await state.session.get(Invoice, invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        if invoice.status == InvoiceStatus.PAID.value:
            raise HTTPException(status_code=400, detail="Invoice already paid")

        invoice.status = InvoiceStatus.PAID.value
        await state.session.commit()

        return ApiResponse(success=True, data={"paid": True})
