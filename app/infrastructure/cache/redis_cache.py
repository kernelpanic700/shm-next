# =============================================================================
# shm-next — Redis Cache
# =============================================================================
"""
Кэш на основе Redis.

Используется для:
- Кэширования данных абонентов
- Rate limiting
- Хранение сессий
- Очередь задач (через Taskiq)
"""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from redis.asyncio import Redis


class RedisCache:
    """
    Обёртка над Redis для кэширования данных.

    Поддерживает:
    - GET/SET с TTL
    - Инкремент/декремент
    - Удаление по паттерну
    - Работа с хэшами
    """

    def __init__(
        self,
        redis_url: str | None = None,
        ttl: int = 300,
    ) -> None:
        self._redis_url = redis_url
        self._default_ttl = ttl
        self._client: Redis | None = None

    async def _get_client(self) -> Redis:
        """Получить Redis клиент (lazy initialization)."""
        if self._client is None:
            self._client = Redis.from_url(
                self._redis_url or "",
                decode_responses=True,
            )
        return self._client

    async def get(self, key: str) -> Any | None:
        """Получить значение по ключу."""
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value is not None:
                return json.loads(value)
            return None
        except Exception:
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | timedelta | None = None,
    ) -> bool:
        """Установить значение с TTL."""
        try:
            client = await self._get_client()
            ttl = ttl or self._default_ttl

            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())

            serialized = json.dumps(value)

            if ttl > 0:
                await client.setex(key, ttl, serialized)
            else:
                await client.set(key, serialized)

            return True
        except Exception:
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """Инкремент значения."""
        try:
            client = await self._get_client()
            return await client.incrby(key, amount)
        except Exception:
            return 0

    async def delete(self, key: str) -> bool:
        """Удалить ключ."""
        try:
            client = await self._get_client()
            return bool(await client.delete(key))
        except Exception:
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Удалить все ключи по паттерну."""
        try:
            client = await self._get_client()
            keys = await client.keys(pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception:
            return 0

    async def exists(self, key: str) -> bool:
        """Проверка существования ключа."""
        try:
            client = await self._get_client()
            return bool(await client.exists(key))
        except Exception:
            return False

    async def hget(self, name: str, key: str) -> Any | None:
        """Получить значение из хэша."""
        try:
            client = await self._get_client()
            value = await client.hget(name, key)
            return json.loads(value) if value else None
        except Exception:
            return None

    async def hset(self, name: str, key: str, value: Any) -> bool:
        """Установить значение в хэш."""
        try:
            client = await self._get_client()
            return bool(await client.hset(name, key, json.dumps(value)))
        except Exception:
            return False

    async def close(self) -> None:
        """Закрыть соединение."""
        if self._client:
            await self._client.close()
            self._client = None

    async def ping(self) -> bool:
        """Проверка доступности Redis."""
        try:
            client = await self._get_client()
            return bool(await client.ping())
        except Exception:
            return False
