# =============================================================================
# shm-next — Integration Tests: Payment Repository
# =============================================================================
from __future__ import annotations

from datetime import datetime, timezone

from app.infrastructure.db.repositories.payment_repo import PaymentRepository


class TestPaymentRepository:

    async def test_create_payment(self, db_session):
        repo = PaymentRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        payment_id = await repo.create(abonent_id=abonent_id, amount=1500.0, currency="RUB", payment_method="card", external_id="ext-001")
        assert payment_id is not None
        retrieved = await repo.get(payment_id)
        assert retrieved is not None
        assert retrieved["abonent_id"] == str(abonent_id)
        assert retrieved["amount"] == 1500.0
        assert retrieved["status"] == "NEW"

    async def test_get_nonexistent_payment(self, db_session):
        repo = PaymentRepository(db_session)
        import uuid
        assert await repo.get(uuid.uuid4()) is None

    async def test_get_by_abonent(self, db_session):
        repo = PaymentRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        for amount in [100, 200, 300]:
            await repo.create(abonent_id=abonent_id, amount=float(amount), currency="RUB", payment_method="cash")
        payments = await repo.get_by_abonent(abonent_id)
        assert len(payments) == 3

    async def test_get_by_abonent_with_date_filter(self, db_session):
        repo = PaymentRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        await repo.create(abonent_id=abonent_id, amount=100.0, currency="RUB", payment_method="cash")
        from_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        payments = await repo.get_by_abonent(abonent_id, from_date=from_date)
        assert len(payments) >= 1

    async def test_confirm_payment(self, db_session):
        repo = PaymentRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        payment_id = await repo.create(abonent_id=abonent_id, amount=500.0, currency="RUB", payment_method="card")
        result = await repo.confirm(payment_id)
        assert result is True
        payment = await repo.get(payment_id)
        assert payment["status"] == "COMPLETED"
        assert payment["completed_at"] is not None

    async def test_confirm_already_completed(self, db_session):
        repo = PaymentRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        payment_id = await repo.create(abonent_id=abonent_id, amount=500.0, currency="RUB", payment_method="card")
        await repo.confirm(payment_id)
        result = await repo.confirm(payment_id)
        assert result is False

    async def test_refund_payment(self, db_session):
        repo = PaymentRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        payment_id = await repo.create(abonent_id=abonent_id, amount=500.0, currency="RUB", payment_method="card")
        await repo.confirm(payment_id)
        result = await repo.refund(payment_id)
        assert result is True
        payment = await repo.get(payment_id)
        assert payment["status"] == "REFUNDED"

    async def test_refund_non_completed(self, db_session):
        repo = PaymentRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        payment_id = await repo.create(abonent_id=abonent_id, amount=500.0, currency="RUB", payment_method="card")
        result = await repo.refund(payment_id)
        assert result is False
