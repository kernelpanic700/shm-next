# =============================================================================
# shm-next — Integration Tests: Payment Repository
# =============================================================================
from __future__ import annotations

from app.infrastructure.db.repositories.payment_repo import PaymentRepository


class TestPaymentRepository:

    async def test_create_payment(self, db_session):
        """Test creating a payment using the repository's create method."""
        repo = PaymentRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        payment_id = await repo.create(
            abonent_id=abonent_id,
            amount=1500.0,
            currency="RUB",
            payment_method="card",
            external_id="ext-001"
        )
        assert payment_id is not None
        retrieved = await repo.get(payment_id)
        assert retrieved is not None
        assert retrieved["abonent_id"] == str(abonent_id)
        assert retrieved["amount"] == 1500.0
        assert retrieved["status"] == "NEW"

    async def test_get_nonexistent_payment(self, db_session):
        """Test getting a non-existent payment returns None."""
        repo = PaymentRepository(db_session)
        import uuid
        assert await repo.get(uuid.uuid4()) is None

    async def test_get_by_abonent(self, db_session):
        """Test getting payments by abonent."""
        repo = PaymentRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        for amount in [100, 200, 300]:
            await repo.create(abonent_id=abonent_id, amount=float(amount), currency="RUB", payment_method="cash")
        payments = await repo.get_by_abonent(abonent_id)
        assert len(payments) == 3