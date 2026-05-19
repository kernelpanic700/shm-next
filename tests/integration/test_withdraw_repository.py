# =============================================================================
# shm-next — Integration Tests: Withdraw Repository
# =============================================================================
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.core.domain.entities.withdraw import Withdraw
from app.core.domain.value_objects import WithdrawStatus
from app.infrastructure.db.repositories.withdraw_repo import WithdrawRepository


class TestWithdrawRepository:

    async def _create_withdraw(self, db_session) -> Withdraw:
        withdraw_repo = WithdrawRepository(db_session)
        withdraw = Withdraw(
            abonent_id=UUID('12345678-1234-5678-1234-567812345678'),
            service_id=UUID('12345678-1234-5678-1234-567812345679'),
            amount=500.0,
            currency="RUB",
            status=WithdrawStatus.PENDING,
            strategy="honest",
        )
        return await withdraw_repo.save(withdraw)

    async def test_create_and_get_withdraw(self, db_session):
        repo = WithdrawRepository(db_session)
        withdraw = Withdraw(
            abonent_id=UUID('12345678-1234-5678-1234-567812345678'),
            service_id=UUID('12345678-1234-5678-1234-567812345679'),
            amount=500.0,
            currency="RUB",
            status=WithdrawStatus.PENDING,
            strategy="honest",
        )
        saved = await repo.save(withdraw)
        assert saved.id is not None
        retrieved = await repo.get(saved.id)
        assert retrieved is not None
        assert retrieved.abonent_id == withdraw.abonent_id
        assert retrieved.service_id == withdraw.service_id
        assert retrieved.amount == 500.0
        assert retrieved.status == WithdrawStatus.PENDING
        assert retrieved.strategy == "honest"

    async def test_get_nonexistent_withdraw(self, db_session):
        repo = WithdrawRepository(db_session)
        import uuid
        result = await repo.get(uuid.uuid4())
        assert result is None

    async def test_get_by_abonent_id(self, db_session):
        repo = WithdrawRepository(db_session)
        # Create a withdraw
        withdraw = await self._create_withdraw(db_session)
        
        # Get withdraws by abonent_id
        withdraws = await repo.get_by_abonent(withdraw.abonent_id)
        assert len(withdraws) >= 1
        assert any(w.id == withdraw.id for w in withdraws)

    async def test_update_withdraw_status(self, db_session):
        repo = WithdrawRepository(db_session)
        withdraw = await self._create_withdraw(db_session)
        
        # Update the withdraw status using domain method
        withdraw.complete()
        updated = await repo.save(withdraw)
        
        assert updated.id == withdraw.id
        assert updated.status == WithdrawStatus.COMPLETED
        assert updated.completed_at is not None
        
        # Verify the update persisted
        retrieved = await repo.get(withdraw.id)
        assert retrieved is not None
        assert retrieved.status == WithdrawStatus.COMPLETED
        assert retrieved.completed_at is not None

    async def test_get_by_status(self, db_session):
        repo = WithdrawRepository(db_session)
        # Create pending withdraw
        pending_withdraw = await self._create_withdraw(db_session)
        
        # Create completed withdraw
        completed_withdraw = Withdraw(
            abonent_id=UUID('12345678-1234-5678-1234-567812345678'),
            service_id=UUID('12345678-1234-5678-1234-567812345679'),
            amount=300.0,
            currency="RUB",
            status=WithdrawStatus.COMPLETED,
            strategy="honest",
            completed_at=datetime.now(timezone.utc),
        )
        await repo.save(completed_withdraw)
        
        # Get only pending withdraws
        pending_withdraws = await repo.get_pending()
        assert len(pending_withdraws) >= 1
        assert any(w.id == pending_withdraw.id for w in pending_withdraws)
        assert not any(w.id == completed_withdraw.id for w in pending_withdraws)