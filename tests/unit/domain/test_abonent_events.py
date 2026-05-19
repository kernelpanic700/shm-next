# =============================================================================
# shm-next — Unit Tests: Abonent Events
# =============================================================================
"""Тесты для событий абонента."""

from __future__ import annotations

from uuid import uuid4

from app.core.domain.events.abonent_events import (
    AbonentActivatedEvent,
    AbonentBlockedEvent,
    AbonentCreatedEvent,
    AbonentUpdatedEvent,
)
from app.core.domain.value_objects.event_type import EventType


class TestAbonentCreatedEvent:
    def test_create(self):
        event = AbonentCreatedEvent(
            abonent_id=str(uuid4()),
            full_name="Иванов Иван",
            phone="+79991234567",
            account_number="12345",
            balance=1000.0,
        )
        assert event.event_type == EventType.ABONENT_CREATED
        assert event.abonent_id is not None
        assert event.full_name == "Иванов Иван"
        assert event.phone == "+79991234567"
        assert event.account_number == "12345"
        assert event.balance == 1000.0
        assert event.currency == "RUB"

    def test_create_with_tariff(self):
        event = AbonentCreatedEvent(
            abonent_id=str(uuid4()),
            full_name="Петров",
            phone="+79990000000",
            account_number="ACC1",
            balance=0,
            tariff_id=str(uuid4()),
        )
        assert event.tariff_id is not None

    def test_to_dict(self):
        event = AbonentCreatedEvent(
            abonent_id=str(uuid4()),
            full_name="Тест",
            phone="+79990000001",
            account_number="T1",
            balance=500,
        )
        d = event.to_dict()
        assert d["event_type"] == "abonent.created"
        assert "abonent_id" not in d  # to_dict returns only base fields
        assert "event_id" in d


class TestAbonentUpdatedEvent:
    def test_create(self):
        event = AbonentUpdatedEvent(
            abonent_id=str(uuid4()),
            changes={"full_name": "Новое имя"},
        )
        assert event.event_type == EventType.ABONENT_UPDATED
        assert event.changes == {"full_name": "Новое имя"}


class TestAbonentBlockedEvent:
    def test_create(self):
        event = AbonentBlockedEvent(
            abonent_id=str(uuid4()),
            reason="Задолженность",
        )
        assert event.event_type == EventType.ABONENT_BLOCKED
        assert event.reason == "Задолженность"

    def test_create_without_reason(self):
        event = AbonentBlockedEvent(abonent_id=str(uuid4()))
        assert event.reason == ""


class TestAbonentActivatedEvent:
    def test_create(self):
        event = AbonentActivatedEvent(abonent_id=str(uuid4()))
        assert event.event_type == EventType.ABONENT_ACTIVATED
