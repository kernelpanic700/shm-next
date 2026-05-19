# =============================================================================
# shm-next — Integration Tests: Withdraw Repository
# =============================================================================
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.core.domain.entities.abonent import Abonent
from app.core.domain.entities.service import UserService
from app.core.domain.entities.withdraw import Withdraw
from app.core.domain.value_objects import Money, ServiceStatus, WithdrawStatus
from app.infrastructure.db.repositories.abonent_repo import AbonentRepository
from app.infrastructure.db.repositories.service_repo import ServiceRepository
from app.infrastructure.db.repositories.withdraw_repo import WithdrawRepository


class TestWithdrawRepository:

    async def _create_abonent(self, db_session) -> Abonent:
        abonent_repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="Абонент Для Списания", phone="+79009998877",
            account_number="91001", balance=Money(5000, "RUB"),
        )
        return await abonent_repo.save(abonent)

    async def _create_service(self, db_session, abonent_id: UUID) -> UserService:
        service_repo = ServiceRepository(db_session)
        service = UserService(
            abonent_id=abonent_id, service_type="voice",
            status=ServiceStatus.ACTIVE, cost=100.0, currency="RUB",
        )
        return await service_repo.save(service)

    async def test_create_and_get_withdraw(self, db_session):
        repo = WithdrawRepository(db_session)
        abonent = await self._create_abonent(db_session)
        service = await self._create_service(db_session, abonent.id)
        withdraw = Withdraw(
            abonent_id=abonent.id, service_id=service.id,
            amount=100.0, currency="RUB",
            status=WithdrawStatus.PENDING, strategy="honest",
        )
        saved = await repo.save(withdraw)
        assert saved.id is not None
        retrieved = await repo.get(saved.id)
        assert retrieved is not None
        assert retrieved.abonent_id == abonent.id
        assert retrieved.service_id == service.id
        assert retrieved.amount == 100.0
        assert retrieved.status == WithdrawStatus.PENDING

    async def test_get_nonexistent_withdraw(self, db_session):
        repo = WithdrawRepository(db_session)
        import uuid
        assert await repo.get(uuid.uuid4()) is None

    async def test_get_by_abonent(self, db_session):
        repo = WithdrawRepository(db_session)
        abonent = await self._create_abonent(db_session)
        service = await self._create_service(db_session, abonent.id)
        for amount in [100, 200, 300]:
            withdraw = Withdraw(
                abonent_id=abonent.id, service_id=service.id,
                amount=float(amount), currency="RUB",
                status=WithdrawStatus.COMPLETED,
            )
            await repo.save(withdraw)
        withdraws = await repo.get_by_abonent(abonent.id)
        assert len(withdraws) == 3

    async def test_get_by_abonent_with_date_filter(self, db_session):
        repo = WithdrawRepository(db_session)
        abonent = await self._create_abonent(db_session)
        service = await self._create_service(db_session, abonent.id)
        old_withdraw = Withdraw(
            abonent_id=abonent.id, service_id=service.id,
            amount=50.0, currency="RUB",
            status=WithdrawStatus.COMPLETED,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        await repo.save(old_withdraw)
        new_withdraw = Withdraw(
            abonent_id=abonent.id, service_id=service.id,
            amount=150.0, currency="RUB",
            status=WithdrawStatus.COMPLETED,
        )
        await repo.save(new_withdraw)
        filtered = await repo.get_by_abonent(
            abonent.id,
            from_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        assert len(filtered) == 1
        assert filtered[0].amount == 150.0

    async def test_get_pending(self, db_session):
        repo = WithdrawRepository(db_session)
        abonent = await self._create_abonent(db_session)
        service = await self._create_service(db_session, abonent.id)
        pending = Withdraw(
            abonent_id=abonent.id, service_id=service.id,
            amount=100.0, currency="RUB",
            status=WithdrawStatus.PENDING,
        )
        completed = Withdraw(
            abonent_id=abonent.id, service_id=service.id,
            amount=200.0, currency="RUB",
            status=WithdrawStatus.COMPLETED,
        )
        await repo.save(pending)
        await repo.save(completed)
        pending_withdraws = await repo.get_pending()
        assert any(w.id == pending.id for w in pending_withdraws)
        assert not any(w.id == completed.id for w in pending_withdraws)

    async def test_get_by_service(self, db_session):
        repo = WithdrawRepository(db_session)
        abonent = await self._create_abonent(db_session)
        service = await self._create_service(db_session, abonent.id)
        for amount in [50, 150]:
            withdraw = Withdraw(
                abonent_id=abonent.id, service_id=service.id,
                amount=float(amount), currency="RUB",
                status=WithdrawStatus.COMPLETED,
            )
            await repo.save(withdraw)
        withdraws = await repo.get_by_service(service.id)
        assert len(withdraws) == 2

    async def test_complete_withdraw(self, db_session):
        repo = WithdrawRepository(db_session)
        abonent = await self._create_abonent(db_session)
        service = await self._create_service(db_session, abonent.id)
        withdraw = Withdraw(
            abonent_id=abonent.id, service_id=service.id,
            amount=100.0, currency="RUB",
            status=WithdrawStatus.PENDING,
        )
        saved = await repo.save(withdraw)
        saved.complete()
        updated = await repo.save(saved)
        assert updated.status == WithdrawStatus.COMPLETED
        assert updated.completed_at is not None

    async def test_fail_withdraw(self, db_session):
        repo = WithdrawRepository(db_session)
        abonent = await self._create_abonent(db_session)
        service = await self._create_service(db_session, abonent.id)
        withdraw = Withdraw(
            abonent_id=abonent.id, service_id=service.id,
            amount=100.0, currency="RUB",
            status=WithdrawStatus.PENDING,
        )
        saved = await repo.save(withdraw)
        saved.fail("Недостаточно средств")
        updated = await repo.save(saved)
        assert updated.status == WithdrawStatus.FAILED
        assert updated.error_message == "Недостаточно средств"
