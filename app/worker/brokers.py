# =============================================================================
# shm-next — Worker: Brokers Configuration
# =============================================================================
"""Настройка брокеров сообщений для Taskiq."""

from __future__ import annotations

from taskiq import TaskiqScheduler
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from app.api.config import AppConfig

config = AppConfig()

# Redis брокер
broker = RedisStreamBroker(config.redis_url)

# Result backend
result_backend = RedisAsyncResultBackend(config.redis_url)

# Планировщик задач
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[],
)
