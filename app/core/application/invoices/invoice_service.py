# =============================================================================
# shm-next - Invoice Application Service
# =============================================================================
"""Application service для сценариев счетов."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.application.payments.payment_service import PaymentService
from app.core.domain.entities.invoice import Invoice, InvoiceStatus
from app.core.domain.repositories.abonent import AbonentRepositoryProtocol
from app.core.domain.repositories.invoice import InvoiceRepositoryProtocol


@dataclass(slots=True)
class InvoiceCreateCommand:
    """Команда создания счёта."""

    abonent_id: UUID
    amount: float
    currency: str = "RUB"
    period_start: datetime | None = None
    period_end: datetime | None = None
    due_date: datetime | None = None
    description: str | None = None
    metadata: dict | None = None
    issue_now: bool = True


@dataclass(slots=True)
class InvoicePaymentResult:
    """Результат оплаты счёта."""

    invoice: Invoice
    payment_id: UUID


class InvoiceService:
    """Сервис сценариев счетов."""

    def __init__(
        self,
        invoice_repo: InvoiceRepositoryProtocol,
        abonent_repo: AbonentRepositoryProtocol,
        payment_service: PaymentService,
    ) -> None:
        self._invoice_repo = invoice_repo
        self._abonent_repo = abonent_repo
        self._payment_service = payment_service

    async def list_invoices(
        self,
        abonent_id: UUID | None = None,
        status: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Invoice], int]:
        if abonent_id is None:
            return await self._invoice_repo.list(
                status=status,
                from_date=from_date,
                to_date=to_date,
                offset=offset,
                limit=limit,
            )

        invoices = await self._invoice_repo.get_by_abonent(
            abonent_id=abonent_id,
            from_date=from_date,
            to_date=to_date,
        )
        if status:
            invoices = [invoice for invoice in invoices if invoice.status == status]

        total = len(invoices)
        return invoices[offset : offset + limit], total

    async def get_invoice(self, invoice_id: UUID) -> Invoice | None:
        return await self._invoice_repo.get(invoice_id)

    async def create_invoice(self, command: InvoiceCreateCommand) -> Invoice:
        abonent = await self._abonent_repo.get(command.abonent_id)
        if abonent is None:
            raise ValueError(f"Abonent {command.abonent_id} not found")

        invoice = Invoice(
            abonent_id=command.abonent_id,
            amount=command.amount,
            currency=command.currency,
            period_start=command.period_start,
            period_end=command.period_end,
            due_date=command.due_date,
            description=command.description,
            metadata=command.metadata,
        )
        if command.issue_now:
            invoice.issue()

        return await self._invoice_repo.save(invoice)

    async def issue_invoice(self, invoice_id: UUID) -> Invoice:
        invoice = await self._get_existing(invoice_id)
        self._ensure_not_paid_or_cancelled(invoice, "issued")
        invoice.issue()
        return await self._invoice_repo.save(invoice)

    async def send_invoice(self, invoice_id: UUID) -> Invoice:
        invoice = await self._get_existing(invoice_id)
        self._ensure_not_paid_or_cancelled(invoice, "sent")
        invoice.mark_sent()
        return await self._invoice_repo.save(invoice)

    async def mark_overdue(self, invoice_id: UUID) -> Invoice:
        invoice = await self._get_existing(invoice_id)
        self._ensure_not_paid_or_cancelled(invoice, "overdue")
        invoice.mark_overdue()
        return await self._invoice_repo.save(invoice)

    async def cancel_invoice(self, invoice_id: UUID) -> Invoice:
        invoice = await self._get_existing(invoice_id)
        if invoice.status == InvoiceStatus.PAID:
            raise ValueError("Paid invoice cannot be cancelled")

        invoice.cancel()
        return await self._invoice_repo.save(invoice)

    async def pay_invoice(
        self,
        invoice_id: UUID,
        payment_method: str = "manual",
        external_id: str | None = None,
    ) -> InvoicePaymentResult:
        invoice = await self._get_existing(invoice_id)
        if invoice.status == InvoiceStatus.PAID:
            raise ValueError("Invoice already paid")
        if invoice.abonent_id is None:
            raise ValueError("Invoice has no abonent")

        payment_external_id = (
            f"invoice:{invoice.id}:{external_id}"
            if external_id
            else f"invoice:{invoice.id}"
        )
        payment = await self._payment_service.create_payment(
            abonent_id=invoice.abonent_id,
            amount=float(invoice.amount),
            currency=invoice.currency,
            payment_method=payment_method,
            external_id=payment_external_id,
        )
        confirmed = await self._payment_service.confirm_payment(payment.id)
        if not confirmed:
            raise ValueError("Payment was not confirmed")

        invoice.mark_paid()
        saved = await self._invoice_repo.save(invoice)
        return InvoicePaymentResult(invoice=saved, payment_id=payment.id)

    async def _get_existing(self, invoice_id: UUID) -> Invoice:
        invoice = await self._invoice_repo.get(invoice_id)
        if invoice is None:
            raise LookupError(f"Invoice {invoice_id} not found")
        return invoice

    @staticmethod
    def _ensure_not_paid_or_cancelled(invoice: Invoice, action: str) -> None:
        if invoice.status == InvoiceStatus.PAID:
            raise ValueError(f"Paid invoice cannot be {action}")
        if invoice.status == InvoiceStatus.CANCELLED:
            raise ValueError(f"Cancelled invoice cannot be {action}")
