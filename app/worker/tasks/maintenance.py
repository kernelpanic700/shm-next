# =============================================================================
# shm-next — Worker Tasks: Maintenance
# =============================================================================
"""Обслуживающие задачи."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.infrastructure.db.unit_of_work import UnitOfWork
from app.worker.brokers import broker


async def retry_failed_spool_tasks(
    max_retries: int = 3,
    uow: UnitOfWork | None = None,
) -> dict:
    """Повторить неудачные SpoolTask."""
    if uow is None:
        uow = UnitOfWork()
    async with uow:
        failed_tasks = await uow.spool.get_failed(max_retries=max_retries)

        for task in failed_tasks:
            task.reset_for_retry()
            await uow.spool.save(task)

        await uow.commit()
        return {"status": "success", "retried": len(failed_tasks)}


async def cleanup_expired_sessions(
    older_than_days: int = 30,
    uow: UnitOfWork | None = None,
) -> dict:
    """Очистить просроченные сессии."""
    if uow is None:
        uow = UnitOfWork()
    async with uow:
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        deleted = await uow.sessions.delete_expired(cutoff)
        await uow.commit()
        return {"status": "success", "deleted": deleted}


# Taskiq задачи
retry_failed_spool_tasks_task = broker.task(retry_failed_spool_tasks, crontab="0 * * * *")  # Каждый час
cleanup_expired_sessions_task = broker.task(cleanup_expired_sessions, crontab="0 3 * * *")  # Каждый день в 3:00
