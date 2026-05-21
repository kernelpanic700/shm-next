# =============================================================================
# shm-next — Worker Tasks: Maintenance
# =============================================================================
"""Обслуживающие задачи."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from taskiq import TaskiqDepends

from app.infrastructure.db.unit_of_work import UnitOfWork
from app.worker.brokers import broker


async def retry_failed_spool_tasks(
    max_retries: int = 3,
    uow: UnitOfWork = TaskiqDepends(UnitOfWork),
) -> dict:
    """Повторить неудачные SpoolTask."""
    async with uow:
        failed_tasks = await uow.spool.get_failed(max_retries=max_retries)

        for task in failed_tasks:
            task.reset_for_retry()
            await uow.spool.save(task)

        await uow.commit()
        return {"status": "success", "retried": len(failed_tasks)}


async def cleanup_expired_sessions(
    older_than_days: int = 30,
    uow: UnitOfWork = TaskiqDepends(UnitOfWork),
) -> dict:
    """Очистить просроченные сессии."""
    async with uow:
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        deleted = await uow.sessions.delete_expired(cutoff)
        await uow.commit()
        return {"status": "success", "deleted": deleted}


# Taskiq задачи
retry_failed_spool_tasks_task = broker.task(retry_failed_spool_tasks)
cleanup_expired_sessions_task = broker.task(cleanup_expired_sessions)
