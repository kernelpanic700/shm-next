# =============================================================================
# shm-next — Integration Tests: Spool Task Repository
# =============================================================================
from __future__ import annotations

from app.infrastructure.db.repositories.spool_repo import SpoolTaskRepository


class TestSpoolTaskRepository:

    async def test_create_task(self, db_session):
        repo = SpoolTaskRepository(db_session)
        task_id = await repo.create_task(
            action_type="send_notification",
            payload={"abonent_id": "123", "message": "Test"},
            priority=5,
            max_retries=3
        )
        assert task_id is not None

    async def test_get_pending_tasks(self, db_session):
        repo = SpoolTaskRepository(db_session)
        await repo.create_task(action_type="send_notification", payload={"msg": "test1"}, priority=50)
        await repo.create_task(action_type="send_notification", payload={"msg": "test2"}, priority=100)
        pending = await repo.get_pending()
        assert len(pending) >= 2

    async def test_get_pending_with_action_filter(self, db_session):
        repo = SpoolTaskRepository(db_session)
        await repo.create_task(action_type="send_notification", payload={}, priority=50)
        await repo.create_task(action_type="call_nas", payload={}, priority=50)
        notifications = await repo.get_pending(action_types=["send_notification"])
        assert all(t["action_type"] == "send_notification" for t in notifications)

    async def test_mark_processing(self, db_session):
        repo = SpoolTaskRepository(db_session)
        task_id = await repo.create_task(action_type="send_notification", payload={})
        result = await repo.mark_processing(task_id, "worker-1")
        assert result is True

    async def test_mark_completed(self, db_session):
        repo = SpoolTaskRepository(db_session)
        task_id = await repo.create_task(action_type="send_notification", payload={})
        result = await repo.mark_completed(task_id, {"status": "sent"})
        assert result is True

    async def test_mark_failed_with_retry(self, db_session):
        repo = SpoolTaskRepository(db_session)
        task_id = await repo.create_task(action_type="send_notification", payload={}, max_retries=3)
        result = await repo.mark_failed(task_id, "Connection timeout", retry_count=1)
        assert result is True

    async def test_mark_failed_max_retries(self, db_session):
        repo = SpoolTaskRepository(db_session)
        task_id = await repo.create_task(action_type="send_notification", payload={}, max_retries=2)
        result = await repo.mark_failed(task_id, "Error", retry_count=3)
        assert result is True

    async def test_move_to_dlq(self, db_session):
        repo = SpoolTaskRepository(db_session)
        _task_id = await repo.create_task(action_type="send_notification", payload={})