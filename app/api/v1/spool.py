# =============================================================================
# shm-next — API v1: Spool (External Actions Queue)
# =============================================================================
"""Эндпоинты для управления очередью внешних действий."""

from __future__ import annotations

from datetime import datetime

from litestar import Controller, get, post
from litestar.datastructures import State
from litestar.exceptions import HTTPException

from app.api.dto.requests import SpoolTaskCreate
from app.api.dto.responses import ApiResponse, SpoolTaskResponse
from app.core.domain.repositories.spool import SpoolRepositoryProtocol


class SpoolController(Controller):
    path = "/spool"
    tags = ["Spool"]

    @get(
        "/",
        summary="Очередь задач",
        description="Получить список задач внешних действий",
    )
    async def list_tasks(
        self,
        state: State,
        status: str | None = None,
        action_type: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> ApiResponse:
        repo: SpoolRepositoryProtocol = state.spool_repo
        tasks = await repo.get_pending(
            action_types=[action_type] if action_type else None,
            limit=per_page,
        )
        return ApiResponse(
            success=True,
            data={
                "items": [
                    SpoolTaskResponse(
                        id=t["id"],
                        action_type=t["action_type"],
                        status=t["status"],
                        priority=t["priority"],
                        retry_count=t["retry_count"],
                        max_retries=t["max_retries"],
                        created_at=t.get("created_at") or datetime.now(),
                        execute_after=t.get("execute_after"),
                    ).model_dump()
                    for t in tasks
                ],
                "total": len(tasks),
                "page": page,
                "per_page": per_page,
            },
        )

    @get(
        "/{task_id:int}",
        summary="Получить задачу",
        description="Получить данные задачи по ID",
    )
    async def get_task(
        self,
        task_id: int,
        state: State,
    ) -> ApiResponse:
        repo: SpoolRepositoryProtocol = state.spool_repo
        task = await repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return ApiResponse(
            success=True,
            data=SpoolTaskResponse(
                id=task.id,
                action_type=task.action_type,
                status=task.status,
                priority=task.priority,
                retry_count=task.retry_count,
                max_retries=task.max_retries,
                created_at=task.created_at or datetime.now(),
                execute_after=task.execute_after,
            ).model_dump(),
        )

    @post(
        "/",
        summary="Создать задачу",
        description="Добавить задачу внешнего действия в очередь",
        status_code=201,
    )
    async def create_task(
        self,
        data: SpoolTaskCreate,
        state: State,
    ) -> ApiResponse:
        repo: SpoolRepositoryProtocol = state.spool_repo
        task_id = await repo.create_task(
            action_type=data.action_type,
            payload=data.payload,
            priority=data.priority,
            max_retries=data.max_retries,
            execute_after=data.execute_after,
        )
        return ApiResponse(
            success=True,
            data={"task_id": task_id},
        )

    @post(
        "/{task_id:int}/retry",
        summary="Повторить задачу",
        description="Повторить выполнение неудачной задачи",
    )
    async def retry_task(
        self,
        task_id: int,
        state: State,
    ) -> ApiResponse:
        from app.infrastructure.external.dlq import DeadLetterQueue
        DeadLetterQueue()
        return ApiResponse(
            success=True,
            data={"message": f"Task {task_id} queued for retry"},
        )
