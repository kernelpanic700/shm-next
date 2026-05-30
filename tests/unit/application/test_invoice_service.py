from uuid import uuid4

import pytest

from app.core.application.invoices import InvoiceCreateCommand, InvoiceService
from app.core.domain.entities.abonent import Abonent
from app.core.domain.entities.invoice import Invoice, InvoiceStatus
from app.core.domain.entities.payment import Payment
from app.core.domain.value_objects import PaymentStatus


class FakeAbonentRepository:
    def __init__(self, abonent: Abonent | None) -> None:
        self.abonent = abonent

    async def get(self, abonent_id):
        if self.abonent is None:
            return None
        return self.abonent if abonent_id == self.abonent.id else None


class FakeInvoiceRepository:
    def __init__(self, invoice: Invoice | None = None) -> None:
        self.invoice = invoice
        self.saved: list[Invoice] = []

    async def get(self, invoice_id):
        return self.invoice if self.invoice and self.invoice.id == invoice_id else None

    async def get_by_abonent(self, abonent_id, from_date=None, to_date=None):
        if self.invoice and self.invoice.abonent_id == abonent_id:
            return [self.invoice]
        return []

    async def list(
        self,
        status=None,
        from_date=None,
        to_date=None,
        offset=0,
        limit=50,
    ):
        invoices = [self.invoice] if self.invoice else []
        if status:
            invoices = [invoice for invoice in invoices if invoice.status == status]
        return invoices[offset : offset + limit], len(invoices)

    async def save(self, invoice: Invoice) -> Invoice:
        self.invoice = invoice
        self.saved.append(invoice)
        return invoice


class FakePaymentService:
    def __init__(self, confirm_result: bool = True) -> None:
        self.payment = Payment(status=PaymentStatus.NEW)
        self.confirm_result = confirm_result
        self.create_calls: list[tuple] = []
        self.confirm_calls: list = []

    async def create_payment(
        self,
        abonent_id,
        amount: float,
        currency: str,
        payment_method: str,
        external_id: str | None = None,
    ) -> Payment:
        self.create_calls.append(
            (abonent_id, amount, currency, payment_method, external_id)
        )
        self.payment = Payment(
            abonent_id=abonent_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            external_id=external_id,
            status=PaymentStatus.NEW,
        )
        return self.payment

    async def confirm_payment(self, payment_id) -> bool:
        self.confirm_calls.append(payment_id)
        return self.confirm_result


def make_service(
    invoice: Invoice | None = None,
    abonent: Abonent | None = None,
    payment_service: FakePaymentService | None = None,
) -> tuple[InvoiceService, FakeInvoiceRepository, FakePaymentService]:
    invoice_repo = FakeInvoiceRepository(invoice)
    service = InvoiceService(
        invoice_repo,
        FakeAbonentRepository(abonent),
        payment_service or FakePaymentService(),
    )
    return service, invoice_repo, service._payment_service


@pytest.mark.asyncio
async def test_list_invoices_without_abonent_uses_global_journal() -> None:
    invoice = Invoice(abonent_id=uuid4(), amount=100, status=InvoiceStatus.ISSUED)
    service, _, _ = make_service(invoice=invoice)

    invoices, total = await service.list_invoices()

    assert invoices == [invoice]
    assert total == 1


@pytest.mark.asyncio
async def test_create_invoice_issues_by_default() -> None:
    abonent = Abonent(id=uuid4())
    service, invoice_repo, _ = make_service(abonent=abonent)

    invoice = await service.create_invoice(
        InvoiceCreateCommand(
            abonent_id=abonent.id,
            amount=500,
            description="Monthly invoice",
            metadata={"source": "unit"},
        )
    )

    assert invoice.status == InvoiceStatus.ISSUED
    assert invoice.description == "Monthly invoice"
    assert invoice.meta == {"source": "unit"}
    assert invoice_repo.saved == [invoice]


@pytest.mark.asyncio
async def test_create_invoice_rejects_missing_abonent() -> None:
    service, invoice_repo, _ = make_service()

    with pytest.raises(ValueError, match="not found"):
        await service.create_invoice(
            InvoiceCreateCommand(
                abonent_id=uuid4(),
                amount=500,
            )
        )

    assert invoice_repo.saved == []


@pytest.mark.asyncio
async def test_status_actions_reject_missing_invoice() -> None:
    service, _, _ = make_service()

    with pytest.raises(LookupError):
        await service.issue_invoice(uuid4())


@pytest.mark.asyncio
async def test_cancel_rejects_paid_invoice() -> None:
    invoice = Invoice(abonent_id=uuid4(), amount=100, status=InvoiceStatus.PAID)
    service, invoice_repo, _ = make_service(invoice=invoice)

    with pytest.raises(ValueError, match="Paid invoice cannot be cancelled"):
        await service.cancel_invoice(invoice.id)

    assert invoice_repo.saved == []


@pytest.mark.asyncio
async def test_pay_invoice_confirms_payment_and_marks_paid() -> None:
    abonent_id = uuid4()
    invoice = Invoice(
        abonent_id=abonent_id,
        amount=1200,
        currency="RUB",
        status=InvoiceStatus.ISSUED,
    )
    payment_service = FakePaymentService()
    service, invoice_repo, _ = make_service(
        invoice=invoice,
        abonent=Abonent(id=abonent_id),
        payment_service=payment_service,
    )

    result = await service.pay_invoice(
        invoice.id,
        payment_method="terminal",
        external_id="provider-1",
    )

    assert result.invoice.status == InvoiceStatus.PAID
    assert result.payment_id == payment_service.payment.id
    assert invoice_repo.saved == [invoice]
    assert payment_service.create_calls == [
        (
            abonent_id,
            1200.0,
            "RUB",
            "terminal",
            f"invoice:{invoice.id}:provider-1",
        )
    ]
    assert payment_service.confirm_calls == [payment_service.payment.id]


@pytest.mark.asyncio
async def test_pay_invoice_rejects_unconfirmed_payment() -> None:
    abonent_id = uuid4()
    invoice = Invoice(
        abonent_id=abonent_id,
        amount=1200,
        currency="RUB",
        status=InvoiceStatus.ISSUED,
    )
    payment_service = FakePaymentService(confirm_result=False)
    service, invoice_repo, _ = make_service(
        invoice=invoice,
        abonent=Abonent(id=abonent_id),
        payment_service=payment_service,
    )

    with pytest.raises(ValueError, match="Payment was not confirmed"):
        await service.pay_invoice(invoice.id)

    assert invoice.status == InvoiceStatus.ISSUED
    assert invoice_repo.saved == []
