# =============================================================================
# shm-next — Dead Letter Queue
# =============================================================================
"""
Dead Letter Queue — хранилище неудачных задач.

Задачи, которые не удалось выполнить после всех попыток,
перемещаются в DLQ для последующего анализа и повторной обработки.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog

from app.infrastructure.cache.redis_cache import RedisCache

logger = structlog.get_logger("dlq")


class DeadLetterQueue:
    """
    Dead Letter Queue на базе Redis.

    Хранит неудачные задачи с информацией об ошибке.
    """

    def __init__(
        self,
        cache: RedisCache | None = None,
        max_size: int = 10000,
    ) -> None:
        self._cache = cache or RedisCache()
        self._max_size = max_size
        self._queue_key = "dlq:tasks"
        self._processed_key = "dlq:processed"

    async def enqueue(
        self,
        action_name: str,
        payload: dict,
        reason: str,
        max_retries: int = 3,
    ) -> str:
        """
        Добавить задачу в DLQ.

        Args:
            action_name: Имя действия
            payload: Параметры действия
            reason: Причина ошибки
            max_retries: Максимальное кол-во повторов

        Returns:
            str: ID записи в DLQ
        """
        dlq_id = str(uuid4())
        entry = {
            "id": dlq_id,
            "action_name": action_name,
            "payload": payload,
            "reason": reason,
            "max_retries": max_retries,
            "created_at": datetime.now(UTC).isoformat(),
            "retry_count": 0,
        }

        try:
            # Сохраняем данные
            await self._cache.set(
                f"dlq:entry:{dlq_id}",
                entry,
                ttl=7 * 24 * 3600,  # 7 дней
            )
            # Добавляем в список
            await self._cache._get_client().lpush(
                self._queue_key, dlq_id
            )
            logger.info("Task added to DLQ", dlq_id=dlq_id, action=action_name)
        except Exception as exc:
            logger.error(
                "Failed to add task to DLQ",
                error=str(exc),
                dlq_id=dlq_id,
            )

        return dlq_id

    async def get_pending(
        self, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Получить задачи из DLQ для повторной обработки.

        Args:
            limit: Максимальное количество задач

        Returns:
            list: Список задач
        """
        try:
            client = await self._cache._get_client()
            dlq_ids = await client.lrange(self._queue_key, 0, limit - 1)

            tasks = []
            for dlq_id in dlq_ids:
                entry = await self._cache.get(f"dlq:entry:{dlq_id}")
                if entry:
                    tasks.append(entry)

            return tasks
        except Exception:
            return []

    async def remove(self, dlq_id: str) -> bool:
        """Удалить задачу из DLQ после успешной повторной обработки."""
        try:
            client = await self._cache._get_client()
            await client.lrem(self._queue_key, 1, dlq_id)
            await self._cache.delete(f"dlq:entry:{dlq_id}")
            return True
        except Exception:
            return False

    async def count(self) -> int:
        """Количество задач в DLQ."""
        try:
            client = await self._cache._get_client()
            return await client.llen(self._queue_key)
        except Exception:
            return 0

    async def clear(self) -> None:
        """Очистить DLQ (только для тестов/разработки!)."""
        try:
            client = await self._cache._get_client()
            await client.delete(self._queue_key)
        except Exception:
            pass
