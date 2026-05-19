# =============================================================================
# shm-next — Unit Tests: SpoolTask
# =============================================================================
"""Тесты для SpoolTask."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.domain.entities.spool_task import SpoolStatus, SpoolTask


class TestSpoolTask:
    """Тесты SpoolTask."""

    def test_create_default(self):
        task = SpoolTask(action_type="test_action")
        assert task.action_type == "test_action"
        assert task.status == SpoolStatus.NEW
        assert task.priority == 50
        assert task.max_retries == 3
        assert task.retry_count == 0

    def test_create_with_params(self):
        task = SpoolTask(
            action_type="send_notification",
            payload={"message": "hello"},
            priority=100,
            max_retries=5,
        )
        assert task.action_type == "send_notification"
        assert task.payload == {"message": "hello"}
        assert task.priority == 100
        assert task.max_retries == 5

    def test_mark_processing(self):
        task = SpoolTask(action_type="test")
        task.mark_processing(worker_id="worker-1")
        assert task.status == SpoolStatus.PROCESSING
        assert task.worker_id == "worker-1"

    def test_mark_success(self):
        task = SpoolTask(action_type="test")
        task.mark_success(result={"status": "ok"})
        assert task.status == SpoolStatus.SUCCESS
        assert task.result == {"status": "ok"}

    def test_mark_failed_retry(self):
        task = SpoolTask(action_type="test", max_retries=3)
        task.mark_failed("Connection error")
        assert task.status == SpoolStatus.FAILED
        assert task.retry_count == 1
        assert task.error_message == "Connection error"

    def test_mark_failed_max_retries(self):
        task = SpoolTask(action_type="test", max_retries=1)
        task.mark_failed("Error 1")
        assert task.status == SpoolStatus.STUCK
        assert task.retry_count == 1

    def test_execute_after(self):
        from datetime import timedelta
        execute_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        task = SpoolTask(action_type="test", execute_after=execute_at)
        assert task.execute_after == execute_at
