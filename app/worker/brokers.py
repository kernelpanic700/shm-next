# =============================================================================
# shm-next — Worker: Brokers Configuration
# =============================================================================
"""Настройка брокеров сообщений для Taskiq."""

from __future__ import annotations

from taskiq import InMemoryBroker, TaskiqScheduler

from app.api.config import AppConfig

config = AppConfig()

try:
    from taskiq_redis import RedisAsyncResultBackend, PubSubBroker
except ModuleNotFoundError:
    broker = InMemoryBroker()
    result_backend = None
else:
    # Redis брокер
    broker = PubSubBroker(config.redis_url)

    # Result backend
    result_backend = RedisAsyncResultBackend(config.redis_url)

# Планировщик задач
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[],
)
