# =============================================================================
# shm-next — Unit Tests: Service Events
# =============================================================================
"""Тесты для событий услуг."""

from __future__ import annotations

from uuid import uuid4

from app.core.domain.events.service_events import (
    ServiceActivatedEvent,
    ServiceDeactivatedEvent,
    ServiceErrorEvent,
)
from app.core.domain.value_objects.event_type import EventType


class TestServiceActivatedEvent:
    def test_create(self):
        event = ServiceActivatedEvent(
            abonent_id=str(uuid4()),
            service_id=str(uuid4()),
            service_type="internet",
        )
        assert event.event_type == EventType.SERVICE_ACTIVATED
        assert event.service_type == "internet"


class TestServiceDeactivatedEvent:
    def test_create(self):
        event = ServiceDeactivatedEvent(
            abonent_id=str(uuid4()),
            service_id=str(uuid4()),
            service_type="voice",
            reason="По запросу абонента",
        )
        assert event.event_type == EventType.SERVICE_DEACTIVATED
        assert event.reason == "По запросу абонента"

    def test_create_without_reason(self):
        event = ServiceDeactivatedEvent(
            abonent_id=str(uuid4()),
            service_id=str(uuid4()),
            service_type="voice",
        )
        assert event.reason == ""


class TestServiceErrorEvent:
    def test_create(self):
        event = ServiceErrorEvent(
            abonent_id=str(uuid4()),
            service_id=str(uuid4()),
            service_type="tv",
            error="Connection timeout",
        )
        assert event.event_type == EventType.SERVICE_ERROR
        assert event.error == "Connection timeout"
