# =============================================================================
# shm-next — Unit Tests: Billing Events
# =============================================================================
"""Тесты для биллинговых событий."""

from __future__ import annotations

from uuid import uuid4

from app.core.domain.events.billing_events import (
    BalanceChangedEvent,
    BillingCycleCompletedEvent,
    BillingCycleStartedEvent,
    PaymentCompletedEvent,
    PaymentFailedEvent,
    WithdrawCompletedEvent,
    WithdrawCreatedEvent,
    WithdrawFailedEvent,
)
from app.core.domain.value_objects.event_type import EventType


class TestBillingCycleStartedEvent:
    def test_create(self):
        event = BillingCycleStartedEvent(
            cycle_id=str(uuid4()),
            abonent_ids=[str(uuid4()), str(uuid4())],
        )
        assert event.event_type == EventType.BILLING_CYCLE_STARTED
        assert len(event.abonent_ids) == 2


class TestBillingCycleCompletedEvent:
    def test_create(self):
        event = BillingCycleCompletedEvent(
            cycle_id=str(uuid4()),
            success_count=10,
            fail_count=2,
        )
        assert event.event_type == EventType.BILLING_CYCLE_COMPLETED
        assert event.success_count == 10
        assert event.fail_count == 2


class TestWithdrawCreatedEvent:
    def test_create(self):
        event = WithdrawCreatedEvent(
            abonent_id=str(uuid4()),
            withdraw_id=str(uuid4()),
            amount=500.0,
            service_type="voice",
        )
        assert event.event_type == EventType.BILLING_WITHDRAW_CREATED
        assert event.amount == 500.0
        assert event.currency == "RUB"
        assert event.service_type == "voice"


class TestWithdrawCompletedEvent:
    def test_create(self):
        event = WithdrawCompletedEvent(
            abonent_id=str(uuid4()),
            withdraw_id=str(uuid4()),
            amount=100.0,
        )
        assert event.event_type == EventType.BILLING_WITHDRAW_COMPLETED
        assert event.amount == 100.0


class TestWithdrawFailedEvent:
    def test_create(self):
        event = WithdrawFailedEvent(
            abonent_id=str(uuid4()),
            withdraw_id=str(uuid4()),
            error="Insufficient funds",
            amount=100.0,
        )
        assert event.event_type == EventType.BILLING_WITHDRAW_FAILED
        assert event.error == "Insufficient funds"


class TestBalanceChangedEvent:
    def test_create(self):
        event = BalanceChangedEvent(
            abonent_id=str(uuid4()),
            old_balance=100.0,
            new_balance=150.0,
            reason="Пополнение",
        )
        assert event.old_balance == 100.0
        assert event.new_balance == 150.0
        assert event.reason == "Пополнение"


class TestPaymentCompletedEvent:
    def test_create(self):
        event = PaymentCompletedEvent(
            abonent_id=str(uuid4()),
            payment_id=str(uuid4()),
            amount=2000.0,
            payment_method="card",
        )
        assert event.event_type == EventType.PAYMENT_COMPLETED
        assert event.amount == 2000.0
        assert event.payment_method == "card"


class TestPaymentFailedEvent:
    def test_create(self):
        event = PaymentFailedEvent(
            abonent_id=str(uuid4()),
            payment_id=str(uuid4()),
            error="Timeout",
            amount=500.0,
        )
        assert event.event_type == EventType.PAYMENT_FAILED
        assert event.error == "Timeout"
