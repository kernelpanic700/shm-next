# =============================================================================
# shm-next — Unit Tests: Session Entity
# =============================================================================
"""Тесты для Session."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.domain.entities.session import Session


class TestSession:
    """Тесты Session."""

    def test_create_default(self):
        session = Session()
        assert session.id is not None
        assert session.is_active is True
        assert session.token_hash == ""

    def test_create_with_params(self):
        session_id = uuid4()
        abonent_id = uuid4()
        session = Session(
            id=session_id,
            abonent_id=abonent_id,
            token_hash="abc123hash",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        assert session.id == session_id
        assert session.abonent_id == abonent_id
        assert session.token_hash == "abc123hash"
        assert session.ip_address == "192.168.1.1"

    def test_is_expired_no_date(self):
        session = Session()
        assert session.is_expired() is False

    def test_is_expired_future(self):
        session = Session(expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        assert session.is_expired() is False

    def test_is_expired_past(self):
        session = Session(expires_at=datetime.now(timezone.utc) - timedelta(hours=1))
        assert session.is_expired() is True

    def test_verify_token_match(self):
        import hashlib
        token = "mysecrettoken"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        session = Session(token_hash=token_hash)
        assert session.verify_token(token) is True

    def test_verify_token_no_match(self):
        session = Session(token_hash="somehash")
        assert session.verify_token("wrongtoken") is False

    def test_expire(self):
        session = Session(is_active=True)
        session.expire()
        assert session.is_active is False
        assert session.version == 2
