# =============================================================================
# shm-next — Worker Application
# =============================================================================
"""Taskiq worker приложение для фоновых задач."""

from __future__ import annotations

from app.worker.brokers import broker, scheduler
from app.worker.tasks import (
    cleanup_expired_sessions_task,
    retry_failed_spool_tasks_task,
    run_billing_cycle_task,
    send_pending_notifications_task,
)

# Регистрация периодических задач в планировщике
scheduler.add_task(
    task=run_billing_cycle_task,
    schedule_id="billing_cycle_daily",
    cron="0 2 * * *",  # Каждый день в 2:00
)

scheduler.add_task(
    task=retry_failed_spool_tasks_task,
    schedule_id="retry_failed_hourly",
    cron="0 * * * *",  # Каждый час
)

scheduler.add_task(
    task=cleanup_expired_sessions_task,
    schedule_id="cleanup_daily",
    cron="0 3 * * *",  # Каждый день в 3:00
)

scheduler.add_task(
    task=send_pending_notifications_task,
    schedule_id="notifications_every_5min",
    cron="*/5 * * * *",  # Каждые 5 минут
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
