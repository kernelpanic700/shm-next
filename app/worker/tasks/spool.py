# =============================================================================
# shm-next — Worker Tasks: Spool
# =============================================================================
"""Обработка SpoolTask."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

from taskiq import TaskiqDepends

from app.infrastructure.db.unit_of_work import UnitOfWork
from app.infrastructure.external.action_executor import ActionExecutor
from app.infrastructure.external.action_registry import ActionRegistry
from app.worker.brokers import broker


def _calculate_execute_after(retry_count: int) -> datetime:
    """Экспоненциальный backoff: 30s, 1m, 2m, 4m, 8m..."""
    delay_seconds = min(30 * (2 ** retry_count), 3600)  # Макс 1 час
    return datetime.now(UTC) + timedelta(seconds=delay_seconds)


async def process_spool_task(
    spool_task_id: UUID,
    uow: UnitOfWork = TaskiqDepends(UnitOfWork),
) -> dict:
    """Обработать SpoolTask с полной логикой статусов и retry."""
    registry = ActionRegistry()
    executor = ActionExecutor(registry=registry, uow=uow)

    async with uow:
        task = await uow.spool.get(spool_task_id)
        if not task:
            return {"status": "error", "message": f"Task {spool_task_id} not found"}

        # Проверка статуса и времени выполнения
        if task.status != "NEW":
            if task.execute_after and task.execute_after > datetime.now(UTC):
                return {"status": "skipped", "message": "Not scheduled yet"}
            if task.status == "COMPLETED":
                return {"status": "skipped", "message": "Already completed"}
            if task.status == "FAILED":
                return {"status": "skipped", "message": "Already failed"}

        # Пометить PROCESSING
        task.status = "PROCESSING"
        task.worker_id = asyncio.current_task().get_name()
        task.started_at = datetime.now(UTC)
        await uow.spool.save(task)
        await uow.commit()

    # Выполнение вне транзакции
    try:
        result = await executor.execute(task.action_type, task.payload)

        async with uow:
            task.status = "COMPLETED"
            task.completed_at = datetime.now(UTC)
            task.result = result
            await uow.spool.save(task)
            await uow.commit()

        return {"status": "success", "result": result}

    except Exception as e:
        async with uow:
            task.retry_count += 1

            if task.retry_count >= task.max_retries:
                task.status = "FAILED"
                task.failed_at = datetime.now(UTC)
                task.error_message = str(e)
            else:
                task.status = "RETRY"
                task.execute_after = _calculate_execute_after(task.retry_count)
                task.error_message = str(e)

            await uow.spool.save(task)
            await uow.commit()

        return {
            "status": "error" if task.status == "FAILED" else "retry",
            "retry_count": task.retry_count,
            "error": str(e),
        }


# Taskiq задача
process_spool_task_task = broker.task(process_spool_task)