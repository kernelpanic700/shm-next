# =============================================================================
# shm-next — Unit Tests: Invoice Entity
# =============================================================================
"""Тесты для Invoice."""

from __future__ import annotations

from uuid import uuid4

from app.core.domain.entities.invoice import Invoice, InvoiceStatus


class TestInvoice:
    """Тесты Invoice."""

    def test_create_default(self):
        invoice = Invoice()
        assert invoice.id is not None
        assert invoice.amount == 0
        assert invoice.status == InvoiceStatus.DRAFT

    def test_create_with_params(self):
        inv_id = uuid4()
        abonent_id = uuid4()
        invoice = Invoice(
            id=inv_id,
            abonent_id=abonent_id,
            amount=1500.00,
            currency="RUB",
            status=InvoiceStatus.ISSUED,
        )
        assert invoice.id == inv_id
        assert invoice.abonent_id == abonent_id
        assert invoice.amount == 1500.00
        assert invoice.currency == "RUB"

    def test_issue(self):
        invoice = Invoice()
        invoice.issue()
        assert invoice.status == InvoiceStatus.ISSUED

    def test_mark_sent(self):
        invoice = Invoice(status=InvoiceStatus.ISSUED)
        invoice.mark_sent()
        assert invoice.status == InvoiceStatus.SENT

    def test_mark_paid(self):
        invoice = Invoice(status=InvoiceStatus.ISSUED)
        invoice.mark_paid()
        assert invoice.status == InvoiceStatus.PAID

    def test_mark_unpaid(self):
        invoice = Invoice(status=InvoiceStatus.PAID)
        invoice.mark_unpaid()
        assert invoice.status == InvoiceStatus.ISSUED

    def test_mark_overdue(self):
        invoice = Invoice(status=InvoiceStatus.ISSUED)
        invoice.mark_overdue()
        assert invoice.status == InvoiceStatus.OVERDUE

    def test_cancel(self):
        invoice = Invoice(status=InvoiceStatus.ISSUED)
        invoice.cancel()
        assert invoice.status == InvoiceStatus.CANCELLED

    def test_version_increment(self):
        invoice = Invoice(version=1)
        invoice.issue()
        assert invoice.version == 2
