# =============================================================================
# shm-next — Taskiq Worker Entry Point
# =============================================================================
"""
Точка входа для воркера задач Taskiq.

Использование:
    taskiq app.worker.app:broker

Брокер подключается к Redis и обрабатывает задачи из очередей:
- billing — критические задачи биллинга
- spool — внешние действия (webhooks, плагины)
- default — остальные задачи
"""

from __future__ import annotations

from taskiq import TaskiqBroker
from taskiq.scheduler import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from app.infrastructure.queue.tasks import register_all_tasks


def create_broker() -> TaskiqBroker:
    """
    Создание и конфигурация брокера задач.
    
    Returns:
        TaskiqBroker: Сконфигурированный брокер
    """
    from app.api.config import get_app_config
    
    config = get_app_config()
    
    broker = TaskiqBroker(
        broker_url=config.taskiq_broker_url,
        result_backend=config.taskiq_result_backend,
        max_retries=10,
        retry_delay=3,
    )
    
    # Регистрация всех задач
    register_all_tasks(broker)
    
    return broker


broker = create_broker()

# Создаём планировщик для периодических задач
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)


async def main() -> None:
    """Entry point для запуска воркера."""
    from taskiq.cli import run_worker
    run_worker(broker=broker, scheduler=scheduler)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
