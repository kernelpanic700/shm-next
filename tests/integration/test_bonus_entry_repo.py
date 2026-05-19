# =============================================================================
# shm-next — Integration Tests: BonusEntry Repository
# =============================================================================
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.domain.entities.bonus_entry import BonusEntry
from app.core.domain.value_objects import Money
from app.infrastructure.db.repositories.bonus_entry_repo import BonusEntryRepository


class TestBonusEntryRepository:

    async def test_create_and_get_bonus_entry(self, db_session):
        repo = BonusEntryRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        entry = BonusEntry(abonent_id=abonent_id, amount=Money(500, "RUB"), reason="Бонус за оплату", source="payment")
        saved = await repo.save(entry)
        assert saved.id is not None
        retrieved = await repo.get(saved.id)
        assert retrieved is not None
        assert retrieved.abonent_id == abonent_id
        assert float(retrieved.amount.amount) == 500.0
        assert retrieved.is_active is True

    async def test_get_nonexistent_bonus_entry(self, db_session):
        repo = BonusEntryRepository(db_session)
        import uuid
        assert await repo.get(uuid.uuid4()) is None

    async def test_get_by_abonent(self, db_session):
        repo = BonusEntryRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        for amount in [100, 200, 300]:
            entry = BonusEntry(abonent_id=abonent_id, amount=Money(amount, "RUB"), reason=f"Бонус {amount}")
            await repo.save(entry)
        entries = await repo.get_by_abonent(abonent_id)
        assert len(entries) == 3

    async def test_get_active(self, db_session):
        repo = BonusEntryRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        active_entry = BonusEntry(abonent_id=abonent_id, amount=Money(100, "RUB"), is_active=True)
        inactive_entry = BonusEntry(abonent_id=abonent_id, amount=Money(200, "RUB"), is_active=False)
        await repo.save(active_entry)
        await repo.save(inactive_entry)
        active_entries = await repo.get_active()
        assert all(e.is_active for e in active_entries)

    async def test_get_expired(self, db_session):
        repo = BonusEntryRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        expired_entry = BonusEntry(abonent_id=abonent_id, amount=Money(100, "RUB"), expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc), is_active=True)
        valid_entry = BonusEntry(abonent_id=abonent_id, amount=Money(200, "RUB"), expires_at=datetime.now(timezone.utc) + timedelta(days=30), is_active=True)
        await repo.save(expired_entry)
        await repo.save(valid_entry)
        expired = await repo.get_expired()
        assert any(e.id == expired_entry.id for e in expired)
        assert not any(e.id == valid_entry.id for e in expired)

    async def test_bonus_expiry_check(self, db_session):
        repo = BonusEntryRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        expired_entry = BonusEntry(abonent_id=abonent_id, amount=Money(100, "RUB"), expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
        saved = await repo.save(expired_entry)
        assert saved.is_expired() is True
        assert saved.can_use() is False

    async def test_deactivate_bonus(self, db_session):
        repo = BonusEntryRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        entry = BonusEntry(abonent_id=abonent_id, amount=Money(100, "RUB"), is_active=True)
        saved = await repo.save(entry)
        saved.expire()
        updated = await repo.save(saved)
        assert updated.is_active is False
