# =============================================================================
# shm-next — Worker Tasks: Spool
# =============================================================================
"""Обработка SpoolTask."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from app.infrastructure.db.unit_of_work import UnitOfWork
from app.infrastructure.external.action_executor import ActionExecutor
from app.infrastructure.external.default_actions import create_default_action_registry
from app.worker.brokers import broker


def _calculate_execute_after(retry_count: int) -> datetime:
    """Экспоненциальный backoff: 30s, 1m, 2m, 4m, 8m..."""
    delay_seconds = min(30 * (2 ** retry_count), 3600)  # Макс 1 час
    return datetime.now(UTC) + timedelta(seconds=delay_seconds)


async def process_spool_task(
    spool_task_id: int,
    uow: UnitOfWork | None = None,
) -> dict:
    """Обработать SpoolTask с полной логикой статусов и retry."""
    if uow is None:
        uow = UnitOfWork()
    executor = ActionExecutor(registry=create_default_action_registry(uow))

    async with uow:
        task = await uow.spool.get_by_id(spool_task_id)
        if not task:
            return {"status": "error", "message": f"Task {spool_task_id} not found"}

        # Проверка статуса и времени выполнения
        if task.execute_after and task.execute_after > datetime.now(UTC):
            return {"status": "skipped", "message": "Not scheduled yet"}
        if task.status in ("SUCCESS", "COMPLETED"):
            return {"status": "skipped", "message": "Already completed"}
        if task.status == "STUCK":
            return {"status": "skipped", "message": "Already stuck"}
        if task.status not in ("NEW", "PENDING", "FAILED", "RETRY"):
            return {"status": "skipped", "message": f"Unsupported status {task.status}"}

        # Пометить PROCESSING
        worker_id = asyncio.current_task().get_name() if asyncio.current_task() else "spool-worker"
        await uow.spool.mark_processing(spool_task_id, worker_id)
        action_type = task.action_type
        payload = task.payload or {}
        retry_count = task.retry_count
        await uow.commit()

    # Выполнение вне транзакции
    try:
        result = await executor.execute(action_type, **payload)
        if not result.success:
            raise RuntimeError(result.error or "Action execution failed")

        async with uow:
            await uow.spool.mark_completed(
                spool_task_id,
                {
                    "result": result.result,
                    "attempts": result.attempts,
                    "duration_ms": result.duration_ms,
                },
            )
            await uow.commit()

        return {"status": "success", "result": result.result}

    except Exception as e:
        async with uow:
            next_retry_count = retry_count + 1
            await uow.spool.mark_failed(
                spool_task_id,
                str(e),
                next_retry_count,
                execute_after=_calculate_execute_after(next_retry_count),
            )
            await uow.commit()

        return {
            "status": "error",
            "retry_count": next_retry_count,
            "error": str(e),
        }


# Taskiq задача
process_spool_task_task = broker.task(process_spool_task)
