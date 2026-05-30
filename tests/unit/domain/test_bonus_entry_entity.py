# =============================================================================
# shm-next — Unit Tests: BonusEntry Entity
# =============================================================================
"""Тесты для BonusEntry."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.domain.entities.bonus_entry import BonusEntry
from app.core.domain.value_objects import Money


class TestBonusEntry:
    """Тесты BonusEntry."""

    def test_create_default(self):
        entry = BonusEntry()
        assert entry.id is not None
        assert entry.is_active is True
        assert entry.source == "manual"

    def test_create_with_params(self):
        entry_id = uuid4()
        abonent_id = uuid4()
        entry = BonusEntry(
            id=entry_id,
            abonent_id=abonent_id,
            amount=Money(500, "RUB"),
            reason="За оплату",
            source="payment",
        )
        assert entry.id == entry_id
        assert entry.abonent_id == abonent_id
        assert entry.amount.amount == 500
        assert entry.reason == "За оплату"
        assert entry.source == "payment"

    def test_is_expired_no_date(self):
        entry = BonusEntry()
        assert entry.is_expired() is False

    def test_is_expired_future(self):
        entry = BonusEntry(expires_at=datetime.now(timezone.utc) + timedelta(days=30))
        assert entry.is_expired() is False

    def test_is_expired_past(self):
        entry = BonusEntry(expires_at=datetime.now(timezone.utc) - timedelta(days=1))
        assert entry.is_expired() is True

    def test_can_use_active_not_expired(self):
        entry = BonusEntry(
            is_active=True,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        assert entry.can_use() is True

    def test_can_use_inactive(self):
        entry = BonusEntry(is_active=False)
        assert entry.can_use() is False

    def test_can_use_expired(self):
        entry = BonusEntry(
            is_active=True,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        assert entry.can_use() is False

    def test_expire(self):
        entry = BonusEntry(is_active=True)
        entry.expire()
        assert entry.is_active is False
        assert entry.version == 2

    def test_consume_partial_bonus(self):
        entry = BonusEntry(amount=Money("100.00", "RUB"))

        used = entry.consume(Money("35.00", "RUB"))

        assert used == Money("35.00", "RUB")
        assert entry.amount == Money("65.00", "RUB")
        assert entry.is_active is True
        assert entry.version == 2

    def test_consume_full_bonus_deactivates_entry(self):
        entry = BonusEntry(amount=Money("50.00", "RUB"))

        used = entry.consume(Money("80.00", "RUB"))

        assert used == Money("50.00", "RUB")
        assert entry.amount == Money("0.00", "RUB")
        assert entry.is_active is False
