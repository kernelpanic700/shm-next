from uuid import uuid4

import pytest
from litestar.exceptions import HTTPException

from app.api.dto.requests import InvoiceCreateRequest
from app.api.v1.invoices import InvoiceController
from app.core.application.invoices import InvoiceService
from app.core.domain.entities.abonent import Abonent
from app.core.domain.entities.invoice import Invoice, InvoiceStatus
from app.core.domain.entities.payment import Payment
from app.core.domain.value_objects import PaymentStatus


class FakeAbonentRepository:
    def __init__(self, abonent_id) -> None:
        self.abonent = Abonent(id=abonent_id)

    async def get(self, abonent_id):
        return self.abonent if abonent_id == self.abonent.id else None


class FakeInvoiceRepository:
    def __init__(self) -> None:
        self.abonent_id = uuid4()
        self.invoice = Invoice(
            abonent_id=self.abonent_id,
            amount=1200,
            currency="RUB",
            status=InvoiceStatus.ISSUED,
        )
        self.saved: list[Invoice] = []

    async def get(self, invoice_id):
        return self.invoice if invoice_id == self.invoice.id else None

    async def get_by_abonent(self, abonent_id, from_date=None, to_date=None):
        return [self.invoice] if abonent_id == self.abonent_id else []

    async def list(
        self,
        status=None,
        from_date=None,
        to_date=None,
        offset=0,
        limit=50,
    ):
        invoices = [self.invoice]
        if status:
            invoices = [invoice for invoice in invoices if invoice.status == status]
        return invoices[offset : offset + limit], len(invoices)

    async def save(self, invoice: Invoice) -> Invoice:
        self.saved.append(invoice)
        return invoice


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.invoices = FakeInvoiceRepository()
        self.abonents = FakeAbonentRepository(self.invoices.abonent_id)
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
        self.close_count += 1

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1


class FakePaymentService:
    def __init__(self) -> None:
        self.payment = Payment(status=PaymentStatus.NEW)
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
        if payment_id != self.payment.id:
            return False
        self.payment.confirm()
        return True


def make_invoice_service(
    uow: FakeUnitOfWork,
    payment_service: FakePaymentService | None = None,
) -> InvoiceService:
    return InvoiceService(
        uow.invoices,
        uow.abonents,
        payment_service or FakePaymentService(),
    )


@pytest.mark.asyncio
async def test_list_invoices_uses_uow_repository() -> None:
    uow = FakeUnitOfWork()
    invoice_service = make_invoice_service(uow)

    response = await InvoiceController.list_invoices.fn(
        None,
        abonent_id=uow.invoices.abonent_id,
        invoice_service=invoice_service,
        status=None,
        from_date=None,
        to_date=None,
        page=1,
        per_page=50,
    )

    assert response.success is True
    assert response.data["total"] == 1
    assert response.data["items"][0]["id"] == str(uow.invoices.invoice.id)


@pytest.mark.asyncio
async def test_list_invoices_without_abonent_returns_global_journal() -> None:
    uow = FakeUnitOfWork()
    invoice_service = make_invoice_service(uow)

    response = await InvoiceController.list_invoices.fn(
        None,
        abonent_id=None,
        invoice_service=invoice_service,
        status=None,
        from_date=None,
        to_date=None,
        page=1,
        per_page=50,
    )

    assert response.success is True
    assert response.data["total"] == 1
    assert response.data["items"][0]["id"] == str(uow.invoices.invoice.id)


@pytest.mark.asyncio
async def test_list_invoices_filters_by_status() -> None:
    uow = FakeUnitOfWork()
    invoice_service = make_invoice_service(uow)

    response = await InvoiceController.list_invoices.fn(
        None,
        abonent_id=uow.invoices.abonent_id,
        invoice_service=invoice_service,
        status=InvoiceStatus.PAID,
        from_date=None,
        to_date=None,
        page=1,
        per_page=50,
    )

    assert response.data["total"] == 0
    assert response.data["items"] == []


@pytest.mark.asyncio
async def test_create_invoice_saves_issued_invoice() -> None:
    uow = FakeUnitOfWork()
    invoice_service = make_invoice_service(uow)

    response = await InvoiceController.create_invoice.fn(
        None,
        data=InvoiceCreateRequest(
            abonent_id=uow.invoices.abonent_id,
            amount=700,
            currency="RUB",
            description="Monthly services",
            metadata={"source": "unit-test"},
        ),
        uow=uow,
        invoice_service=invoice_service,
    )

    assert response.abonent_id == uow.invoices.abonent_id
    assert response.amount == 700
    assert response.status == InvoiceStatus.ISSUED
    assert response.description == "Monthly services"
    assert response.metadata == {"source": "unit-test"}
    assert uow.invoices.saved[-1].status == InvoiceStatus.ISSUED
    assert uow.commit_count == 1


@pytest.mark.asyncio
async def test_create_invoice_returns_404_for_missing_abonent() -> None:
    uow = FakeUnitOfWork()
    invoice_service = make_invoice_service(uow)

    with pytest.raises(HTTPException) as exc_info:
        await InvoiceController.create_invoice.fn(
            None,
            data=InvoiceCreateRequest(
                abonent_id=uuid4(),
                amount=700,
            ),
            uow=uow,
            invoice_service=invoice_service,
        )

    assert exc_info.value.status_code == 404
    assert uow.invoices.saved == []
    assert uow.commit_count == 0


@pytest.mark.asyncio
async def test_get_invoice_returns_404_when_missing() -> None:
    uow = FakeUnitOfWork()
    invoice_service = make_invoice_service(uow)

    with pytest.raises(HTTPException) as exc_info:
        await InvoiceController.get_invoice.fn(
            None,
            invoice_id=uuid4(),
            invoice_service=invoice_service,
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_issue_invoice_changes_status() -> None:
    uow = FakeUnitOfWork()
    invoice_service = make_invoice_service(uow)
    uow.invoices.invoice = Invoice(
        abonent_id=uow.invoices.abonent_id,
        amount=1200,
        status=InvoiceStatus.DRAFT,
    )

    response = await InvoiceController.issue_invoice.fn(
        None,
        invoice_id=uow.invoices.invoice.id,
        uow=uow,
        invoice_service=invoice_service,
    )

    assert response.status == InvoiceStatus.ISSUED
    assert uow.invoices.saved == [uow.invoices.invoice]
    assert uow.commit_count == 1


@pytest.mark.asyncio
async def test_send_invoice_changes_status() -> None:
    uow = FakeUnitOfWork()
    invoice_service = make_invoice_service(uow)

    response = await InvoiceController.send_invoice.fn(
        None,
        invoice_id=uow.invoices.invoice.id,
        uow=uow,
        invoice_service=invoice_service,
    )

    assert response.status == InvoiceStatus.SENT
    assert uow.invoices.saved == [uow.invoices.invoice]
    assert uow.commit_count == 1


@pytest.mark.asyncio
async def test_mark_invoice_overdue_changes_status() -> None:
    uow = FakeUnitOfWork()
    invoice_service = make_invoice_service(uow)

    response = await InvoiceController.mark_invoice_overdue.fn(
        None,
        invoice_id=uow.invoices.invoice.id,
        uow=uow,
        invoice_service=invoice_service,
    )

    assert response.status == InvoiceStatus.OVERDUE
    assert uow.invoices.saved == [uow.invoices.invoice]
    assert uow.commit_count == 1


@pytest.mark.asyncio
async def test_cancel_invoice_changes_status() -> None:
    uow = FakeUnitOfWork()
    invoice_service = make_invoice_service(uow)

    response = await InvoiceController.cancel_invoice.fn(
        None,
        invoice_id=uow.invoices.invoice.id,
        uow=uow,
        invoice_service=invoice_service,
    )

    assert response.status == InvoiceStatus.CANCELLED
    assert uow.invoices.saved == [uow.invoices.invoice]
    assert uow.commit_count == 1


@pytest.mark.asyncio
async def test_cancel_invoice_rejects_paid_invoice() -> None:
    uow = FakeUnitOfWork()
    invoice_service = make_invoice_service(uow)
    uow.invoices.invoice.mark_paid()

    with pytest.raises(HTTPException) as exc_info:
        await InvoiceController.cancel_invoice.fn(
            None,
            invoice_id=uow.invoices.invoice.id,
            uow=uow,
            invoice_service=invoice_service,
        )

    assert exc_info.value.status_code == 400
    assert uow.invoices.saved == []
    assert uow.commit_count == 0


@pytest.mark.asyncio
async def test_pay_invoice_marks_invoice_paid_and_commits() -> None:
    uow = FakeUnitOfWork()
    payment_service = FakePaymentService()
    invoice_service = make_invoice_service(uow, payment_service)

    response = await InvoiceController.pay_invoice.fn(
        None,
        invoice_id=uow.invoices.invoice.id,
        uow=uow,
        invoice_service=invoice_service,
        payment_method="terminal",
        external_id="invoice-pay-1",
    )

    assert response.success is True
    assert response.data == {"paid": True, "payment_id": str(payment_service.payment.id)}
    assert uow.invoices.invoice.status == InvoiceStatus.PAID
    assert uow.invoices.saved == [uow.invoices.invoice]
    assert payment_service.create_calls == [
        (
            uow.invoices.invoice.abonent_id,
            1200.0,
            "RUB",
            "terminal",
            f"invoice:{uow.invoices.invoice.id}:invoice-pay-1",
        )
    ]
    assert payment_service.confirm_calls == [payment_service.payment.id]
    assert uow.commit_count == 1


@pytest.mark.asyncio
async def test_pay_invoice_rejects_already_paid() -> None:
    uow = FakeUnitOfWork()
    payment_service = FakePaymentService()
    invoice_service = make_invoice_service(uow, payment_service)
    uow.invoices.invoice.mark_paid()

    with pytest.raises(HTTPException) as exc_info:
        await InvoiceController.pay_invoice.fn(
            None,
            invoice_id=uow.invoices.invoice.id,
            uow=uow,
            invoice_service=invoice_service,
            payment_method="manual",
            external_id=None,
        )

    assert exc_info.value.status_code == 400
    assert uow.rollback_count == 0
    assert payment_service.create_calls == []
