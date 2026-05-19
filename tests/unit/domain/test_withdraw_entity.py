# =============================================================================
# shm-next — Unit Tests: Withdraw Entity
# =============================================================================
"""Тесты для Withdraw."""

from __future__ import annotations

from uuid import uuid4

from app.core.domain.entities.withdraw import Withdraw
from app.core.domain.value_objects import WithdrawStatus


class TestWithdraw:
    """Тесты Withdraw."""

    def test_create_default(self):
        w = Withdraw()
        assert w.id is not None
        assert w.abonent_id is None
        assert w.service_id is None
        assert w.amount == 0
        assert w.currency == "RUB"
        assert w.status == WithdrawStatus.PENDING
        assert w.strategy == "honest"
        assert w.error_message is None
        assert w.version == 1

    def test_create_with_params(self):
        wid = uuid4()
        abonent_id = uuid4()
        service_id = uuid4()
        w = Withdraw(
            id=wid,
            abonent_id=abonent_id,
            service_id=service_id,
            amount=500.0,
            currency="RUB",
            status=WithdrawStatus.PENDING,
            strategy="prepaid",
        )
        assert w.id == wid
        assert w.abonent_id == abonent_id
        assert w.service_id == service_id
        assert w.amount == 500.0
        assert w.currency == "RUB"
        assert w.strategy == "prepaid"

    def test_complete(self):
        w = Withdraw(amount=100.0)
        initial_version = w.version
        w.complete()
        assert w.status == WithdrawStatus.COMPLETED
        assert w.completed_at is not None
        assert w.version == initial_version + 1

    def test_fail(self):
        w = Withdraw(amount=100.0)
        initial_version = w.version
        w.fail("Insufficient funds")
        assert w.status == WithdrawStatus.FAILED
        assert w.error_message == "Insufficient funds"
        assert w.version == initial_version + 1

    def test_fail_updates_timestamp(self):
        import time

        w = Withdraw(amount=100.0)
        old_updated = w.updated_at
        time.sleep(0.01)
        w.fail("Error")
        assert w.updated_at > old_updated
