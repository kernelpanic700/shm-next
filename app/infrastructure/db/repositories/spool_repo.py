# =============================================================================
# shm-next — Spool Task Repository
# =============================================================================
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.repositories.spool import SpoolRepositoryProtocol
from app.infrastructure.db.models import SpoolTaskModel


class SpoolTaskRepository(SpoolRepositoryProtocol):
    """Репозиторий задач внешних действий."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_task(
        self,
        action_type: str,
        payload: dict,
        priority: int = 50,
        max_retries: int = 3,
        execute_after: datetime | None = None,
    ) -> UUID:
        """Создать задачу."""
        task = SpoolTaskModel(
            action_type=action_type,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
            execute_after=execute_after,
            status="NEW",
        )

        self._session.add(task)
        await self._session.flush()
        return task.id

    async def get_pending(
        self,
        action_types: list[str] | None = None,
        limit: int = 100,
    ) -> list:
        """Получить задачи, ожидающие выполнения."""
        stmt = select(SpoolTaskModel).where(
            SpoolTaskModel.status.in_(["NEW", "PENDING", "FAILED"])
        )

        if action_types:
            stmt = stmt.where(SpoolTaskModel.action_type.in_(action_types))

        stmt = (
            stmt.order_by(SpoolTaskModel.priority.desc())
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        tasks = result.scalars().all()

        return [
            {
                "id": t.id,
                "action_type": t.action_type,
                "payload": t.payload,
                "priority": t.priority,
                "status": t.status,
                "retry_count": t.retry_count,
                "max_retries": t.max_retries,
                "created_at": t.created_at or datetime.now(),
                "execute_after": t.execute_after,
            }
            for t in tasks
        ]

    async def mark_processing(self, task_id: UUID, worker_id: str) -> bool:
        """Отметить задачу как выполняемую."""
        task = await self._session.get(SpoolTaskModel, task_id)

        if task and task.status in ("NEW", "PENDING", "FAILED"):
            task.status = "PROCESSING"
            task.worker_id = worker_id
            await self._session.flush()
            return True
        return False

    async def mark_completed(self, task_id: UUID, result: dict | None = None) -> bool:
        """Отметить задачу как завершённую."""
        task = await self._session.get(SpoolTaskModel, task_id)

        if task:
            task.status = "SUCCESS"
            task.result = result
            await self._session.flush()
            return True
        return False

    async def mark_failed(
        self, task_id: UUID, error: str, retry_count: int
    ) -> bool:
        """Отметить задачу как неудачную."""
        task = await self._session.get(SpoolTaskModel, task_id)

        if task:
            task.retry_count = retry_count
            task.error_message = error

            if retry_count >= task.max_retries:
                task.status = "STUCK"
            else:
                task.status = "FAILED"

            await self._session.flush()
            return True
        return False

    async def move_to_dlq(self, task_id: UUID, error: str) -> bool:
        """Переместить задачу в Dead Letter Queue."""
        task = await self._session.get(SpoolTaskModel, task_id)

        if task:
            task.status = "STUCK"
            task.error_message = error
            await self._session.flush()
            return True
        return False
