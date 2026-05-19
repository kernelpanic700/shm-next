# =============================================================================
# shm-next — Integration Tests: Session Repository
# =============================================================================
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.domain.entities.session import Session
from app.infrastructure.db.repositories.session_repo import SessionRepository


class TestSessionRepository:

    async def test_create_and_get_session(self, db_session):
        repo = SessionRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        session = Session(abonent_id=abonent_id, token_hash="abc123hash", ip_address="192.168.1.1", user_agent="Mozilla/5.0", expires_at=datetime.now(timezone.utc) + timedelta(hours=1), is_active=True)
        saved = await repo.save(session)
        assert saved.id is not None
        retrieved = await repo.get(saved.id)
        assert retrieved is not None
        assert retrieved.token_hash == "abc123hash"
        assert retrieved.abonent_id == abonent_id

    async def test_get_nonexistent_session(self, db_session):
        repo = SessionRepository(db_session)
        import uuid
        assert await repo.get(uuid.uuid4()) is None

    async def test_get_by_token_hash(self, db_session):
        repo = SessionRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        session = Session(abonent_id=abonent_id, token_hash="unique_hash_123", expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        await repo.save(session)
        retrieved = await repo.get_by_token_hash("unique_hash_123")
        assert retrieved is not None
        assert retrieved.token_hash == "unique_hash_123"

    async def test_get_by_token_hash_not_found(self, db_session):
        repo = SessionRepository(db_session)
        assert await repo.get_by_token_hash("nonexistent_hash") is None

    async def test_get_active_by_abonent(self, db_session):
        repo = SessionRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        for i in range(3):
            session = Session(abonent_id=abonent_id, token_hash=f"hash_{i}", is_active=True, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
            await repo.save(session)
        active_sessions = await repo.get_active_by_abonent(abonent_id)
        assert len(active_sessions) == 3

    async def test_get_active_by_abonent_includes_inactive(self, db_session):
        repo = SessionRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        active_session = Session(abonent_id=abonent_id, token_hash="active_hash", is_active=True, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        inactive_session = Session(abonent_id=abonent_id, token_hash="inactive_hash", is_active=False, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        await repo.save(active_session)
        await repo.save(inactive_session)
        active_sessions = await repo.get_active_by_abonent(abonent_id)
        assert len(active_sessions) == 1
        assert active_sessions[0].token_hash == "active_hash"

    async def test_cleanup_expired(self, db_session):
        repo = SessionRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        expired_session = Session(abonent_id=abonent_id, token_hash="expired_hash", is_active=True, expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
        valid_session = Session(abonent_id=abonent_id, token_hash="valid_hash", is_active=True, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        await repo.save(expired_session)
        await repo.save(valid_session)
        deleted_count = await repo.cleanup_expired()
        assert deleted_count >= 1
        retrieved = await repo.get(expired_session.id)
        assert retrieved is None or not retrieved.is_active
        valid_retrieved = await repo.get(valid_session.id)
        assert valid_retrieved is not None

    async def test_session_expiry_check(self, db_session):
        repo = SessionRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        expired_session = Session(abonent_id=abonent_id, token_hash="expired", expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
        saved = await repo.save(expired_session)
        assert saved.is_expired() is True

    async def test_verify_token(self, db_session):
        repo = SessionRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        session = Session(abonent_id=abonent_id, token_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        saved = await repo.save(session)
        assert saved.verify_token("") is True
        assert saved.verify_token("wrong_token") is False

    async def test_expire_session(self, db_session):
        repo = SessionRepository(db_session)
        import uuid
        abonent_id = uuid.uuid4()
        session = Session(abonent_id=abonent_id, token_hash="hash", is_active=True, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        saved = await repo.save(session)
        saved.expire()
        updated = await repo.save(saved)
        assert updated.is_active is False
