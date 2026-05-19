# =============================================================================
# shm-next — Unit Tests: Event Bus
# =============================================================================
"""Тесты для EventBus."""

from __future__ import annotations

import pytest

from app.core.domain.events.event import DomainEvent, EventMetadata
from app.core.domain.value_objects.event_type import EventType
from app.core.services.event_bus import EventBus


class TestEventMetadata:
    """Тесты EventMetadata."""

    def test_create_default(self):
        meta = EventMetadata()
        assert meta.correlation_id is not None
        assert meta.causation_id is None

    def test_create_with_values(self):
        meta = EventMetadata(
            correlation_id="test-123",
            causation_id="cause-456",
            user_id="user-1",
            ip_address="127.0.0.1",
        )
        assert meta.correlation_id == "test-123"
        assert meta.causation_id == "cause-456"

    def test_to_dict(self):
        meta = EventMetadata(correlation_id="test-123")
        d = meta.to_dict()
        assert d["correlation_id"] == "test-123"


class TestDomainEvent:
    """Тесты DomainEvent."""

    def test_create(self):
        event = DomainEvent(EventType.ABONENT_CREATED)
        assert event.event_id is not None
        assert event.event_type == EventType.ABONENT_CREATED
        assert event.timestamp is not None

    def test_to_dict(self):
        event = DomainEvent(EventType.ABONENT_CREATED)
        d = event.to_dict()
        assert d["event_type"] == "abonent.created"
        assert "event_id" in d
        assert "timestamp" in d


class TestEventBus:
    """Тесты EventBus."""

    @pytest.mark.asyncio
    async def test_publish_no_handlers(self):
        bus = EventBus()
        event = DomainEvent(EventType.ABONENT_CREATED)
        results = await bus.publish(event)
        assert results == []

    @pytest.mark.asyncio
    async def test_publish_with_handler(self):
        bus = EventBus()
        handler_called = []

        async def handler(event):
            handler_called.append(event.event_type.value)

        bus.subscribe("abonent.created", handler)
        event = DomainEvent(EventType.ABONENT_CREATED)
        results = await bus.publish(event)

        assert len(handler_called) == 1
        assert handler_called[0] == "abonent.created"
        assert results[0]["success"] is True

    @pytest.mark.asyncio
    async def test_publish_sync_handler(self):
        bus = EventBus()
        handler_called = []

        def handler(event):
            handler_called.append(event.event_type.value)

        bus.subscribe("abonent.created", handler)
        event = DomainEvent(EventType.ABONENT_CREATED)
        results = await bus.publish(event)

        assert len(handler_called) == 1
        assert results[0]["success"] is True

    @pytest.mark.asyncio
    async def test_handler_failure(self):
        bus = EventBus()

        def failing_handler(event):
            raise ValueError("Test error")

        bus.subscribe("abonent.created", failing_handler)
        event = DomainEvent(EventType.ABONENT_CREATED)
        results = await bus.publish(event)

        assert results[0]["success"] is False
        assert "error" in results[0]

    def test_unsubscribe(self):
        bus = EventBus()

        def handler(event):
            pass

        bus.subscribe("abonent.created", handler)
        bus.unsubscribe("test.event", handler)
        assert "test.event" not in bus._handlers or handler not in bus._handlers["test.event"]

    def test_clear(self):
        bus = EventBus()

        def handler(event):
            pass

        bus.subscribe("abonent.created", handler)
        bus.clear()
        assert len(bus._handlers) == 0
