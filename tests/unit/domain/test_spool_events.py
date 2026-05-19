# =============================================================================
# shm-next — Unit Tests: Spool Events
# =============================================================================
"""Тесты для событий очереди внешних действий."""

from __future__ import annotations

from uuid import uuid4

from app.core.domain.events.spool_events import (
    SpoolTaskCompletedEvent,
    SpoolTaskCreatedEvent,
    SpoolTaskFailedEvent,
    SpoolTaskMovedToDLQEvent,
    SpoolTaskStartedEvent,
)
from app.core.domain.value_objects.event_type import EventType


class TestSpoolTaskCreatedEvent:
    def test_create(self):
        event = SpoolTaskCreatedEvent(
            task_id=1,
            action_type="send_notification",
            abonent_id=str(uuid4()),
            priority=100,
        )
        assert event.event_type == EventType.SPOOL_TASK_CREATED
        assert event.task_id == 1
        assert event.action_type == "send_notification"
        assert event.priority == 100

    def test_create_without_abonent(self):
        event = SpoolTaskCreatedEvent(task_id=2, action_type="sync")
        assert event.abonent_id is None


class TestSpoolTaskStartedEvent:
    def test_create(self):
        event = SpoolTaskStartedEvent(
            task_id=1,
            worker_id="worker-1",
            action_type="send_notification",
        )
        assert event.event_type == EventType.SPOOL_TASK_STARTED
        assert event.worker_id == "worker-1"


class TestSpoolTaskCompletedEvent:
    def test_create(self):
        event = SpoolTaskCompletedEvent(
            task_id=1,
            action_type="send_notification",
            result={"status": "ok"},
        )
        assert event.event_type == EventType.SPOOL_TASK_COMPLETED
        assert event.result == {"status": "ok"}

    def test_create_without_result(self):
        event = SpoolTaskCompletedEvent(task_id=2, action_type="sync")
        assert event.result is None


class TestSpoolTaskFailedEvent:
    def test_create(self):
        event = SpoolTaskFailedEvent(
            task_id=1,
            action_type="send_notification",
            error="Connection error",
            retry_count=2,
            max_retries=3,
        )
        assert event.event_type == EventType.SPOOL_TASK_FAILED
        assert event.error == "Connection error"
        assert event.retry_count == 2


class TestSpoolTaskMovedToDLQEvent:
    def test_create(self):
        event = SpoolTaskMovedToDLQEvent(
            task_id=1,
            action_type="send_notification",
            error="Max retries exceeded",
        )
        assert event.event_type == EventType.SPOOL_TASK_DLQ
        assert event.error == "Max retries exceeded"
