# =============================================================================
# shm-next — Worker Application
# =============================================================================
"""Taskiq worker приложение для фоновых задач."""

from __future__ import annotations

from app.worker.brokers import broker, scheduler

# Импортируем задачи для регистрации в брокере
# Расписание задач настраивается через crontab в task-декораторах
from app.worker.tasks import (  # noqa: F401
    cleanup_expired_sessions_task,
    process_spool_task_task,
    retry_failed_spool_tasks_task,
    run_billing_cycle_task,
    run_shm_auto_renewal_task,
    send_pending_notifications_task,
)


@broker.on_event("startup")
async def startup() -> None:
    """Инициализация при старте worker'а."""
    await broker.startup()
    await scheduler.startup()


@broker.on_event("shutdown")
async def shutdown() -> None:
    """Остановка worker'а."""
    await scheduler.shutdown()
    await broker.shutdown()
