# =============================================================================
# shm-next — Integration Tests: Invoice Repository
# =============================================================================
from __future__ import annotations

from datetime import datetime, timezone

from app.core.domain.entities.invoice import Invoice, InvoiceStatus
from app.infrastructure.db.repositories.invoice_repo import InvoiceRepository


class TestInvoiceRepository:

    async def test_create_and_get_invoice(self, db_session):
        repo = InvoiceRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        invoice = Invoice(abonent_id=abonent_id, amount=1500.0, currency="RUB", status=InvoiceStatus.ISSUED, period_start=datetime(2025, 1, 1, tzinfo=timezone.utc), period_end=datetime(2025, 1, 31, tzinfo=timezone.utc), due_date=datetime(2025, 2, 10, tzinfo=timezone.utc), description="Счёт за январь")
        saved = await repo.save(invoice)
        assert saved.id is not None
        retrieved = await repo.get(saved.id)
        assert retrieved is not None
        assert retrieved.amount == 1500.0
        assert retrieved.status == InvoiceStatus.ISSUED

    async def test_get_nonexistent_invoice(self, db_session):
        repo = InvoiceRepository(db_session)
        import uuid
        assert await repo.get(uuid.uuid4()) is None

    async def test_get_by_abonent(self, db_session):
        repo = InvoiceRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        for month in range(1, 4):
            invoice = Invoice(abonent_id=abonent_id, amount=float(1000 * month), currency="RUB", status=InvoiceStatus.ISSUED, period_start=datetime(2025, month, 1, tzinfo=timezone.utc), period_end=datetime(2025, month, 28, tzinfo=timezone.utc))
            await repo.save(invoice)
        invoices = await repo.get_by_abonent(abonent_id)
        assert len(invoices) == 3

    async def test_get_by_abonent_with_date_filter(self, db_session):
        repo = InvoiceRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        old_invoice = Invoice(abonent_id=abonent_id, amount=500.0, currency="RUB", status=InvoiceStatus.PAID, period_start=datetime(2024, 1, 1, tzinfo=timezone.utc), period_end=datetime(2024, 1, 31, tzinfo=timezone.utc))
        new_invoice = Invoice(abonent_id=abonent_id, amount=1000.0, currency="RUB", status=InvoiceStatus.ISSUED, period_start=datetime(2025, 6, 1, tzinfo=timezone.utc), period_end=datetime(2025, 6, 30, tzinfo=timezone.utc))
        await repo.save(old_invoice)
        await repo.save(new_invoice)
        filtered = await repo.get_by_abonent(abonent_id, from_date=datetime(2025, 1, 1, tzinfo=timezone.utc))
        assert len(filtered) >= 1

    async def test_get_unpaid(self, db_session):
        repo = InvoiceRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        draft = Invoice(abonent_id=abonent_id, amount=100.0, currency="RUB", status=InvoiceStatus.DRAFT)
        issued = Invoice(abonent_id=abonent_id, amount=200.0, currency="RUB", status=InvoiceStatus.ISSUED)
        paid = Invoice(abonent_id=abonent_id, amount=300.0, currency="RUB", status=InvoiceStatus.PAID)
        await repo.save(draft)
        await repo.save(issued)
        await repo.save(paid)
        unpaid = await repo.get_unpaid()
        unpaid_ids = {i.id for i in unpaid}
        assert draft.id in unpaid_ids
        assert issued.id in unpaid_ids
        assert paid.id not in unpaid_ids

    async def test_get_overdue(self, db_session):
        repo = InvoiceRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        overdue_invoice = Invoice(abonent_id=abonent_id, amount=100.0, currency="RUB", status=InvoiceStatus.OVERDUE, due_date=datetime(2020, 1, 1, tzinfo=timezone.utc))
        await repo.save(overdue_invoice)
        overdue = await repo.get_overdue()
        assert any(o.id == overdue_invoice.id for o in overdue)

    async def test_issue_invoice(self, db_session):
        repo = InvoiceRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        invoice = Invoice(abonent_id=abonent_id, amount=500.0, currency="RUB", status=InvoiceStatus.DRAFT)
        saved = await repo.save(invoice)
        saved.issue()
        updated = await repo.save(saved)
        assert updated.status == InvoiceStatus.ISSUED

    async def test_mark_paid(self, db_session):
        repo = InvoiceRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        invoice = Invoice(abonent_id=abonent_id, amount=500.0, currency="RUB", status=InvoiceStatus.ISSUED)
        saved = await repo.save(invoice)
        saved.mark_paid()
        updated = await repo.save(saved)
        assert updated.status == InvoiceStatus.PAID

    async def test_mark_overdue(self, db_session):
        repo = InvoiceRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        invoice = Invoice(abonent_id=abonent_id, amount=500.0, currency="RUB", status=InvoiceStatus.ISSUED, due_date=datetime(2020, 1, 1, tzinfo=timezone.utc))
        saved = await repo.save(invoice)
        saved.mark_overdue()
        updated = await repo.save(saved)
        assert updated.status == InvoiceStatus.OVERDUE
