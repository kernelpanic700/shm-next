# =============================================================================
# shm-next — Event Bus
# =============================================================================
"""
Шина событий — центральный механизм публикации/подписки.

Обеспечивает:
- Публикацию доменных событий
- Синхронные и асинхронные обработчики
- Dead Letter Queue для неудачных обработчиков
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

import structlog

from app.core.domain.events.event import DomainEvent

logger = structlog.get_logger("event_bus")


Handler = Callable[[DomainEvent], Any | Awaitable[Any]]


class EventBus:
    """
    Шина событий.

    Подписчики регистрируются на типы событий.
    При публикации события вызываются все подписчики.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._middlewares: list[Callable] = []

    def subscribe(
        self,
        event_type: str,
        handler: Handler,
    ) -> None:
        """
        Подписаться на событие.

        Args:
            event_type: Тип события (строка)
            handler: Функция-обработчик
        """
        self._handlers[event_type].append(handler)
        logger.info("Handler subscribed", event_type=event_type)

    def unsubscribe(
        self,
        event_type: str,
        handler: Handler,
    ) -> None:
        """Отписаться от события."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def publish(self, event: DomainEvent) -> list[dict]:
        """
        Опубликовать событие.

        Args:
            event: Доменное событие

        Returns:
            list: Результаты обработки
        """
        event_type = event.event_type.value
        results = []

        logger.info(
            "Event published",
            event_type=event_type,
            event_id=event.event_id,
        )

        handlers = self._handlers.get(event_type, [])

        for handler in handlers:
            try:
                result = handler(event)
                if hasattr(result, "__await__"):
                    result = await result
                results.append({"handler": handler.__name__, "success": True, "result": result})
                logger.debug(
                    "Handler executed successfully",
                    handler=handler.__name__,
                    event_type=event_type,
                )
            except Exception as exc:
                logger.error(
                    "Handler failed",
                    handler=handler.__name__,
                    event_type=event_type,
                    error=str(exc),
                )
                results.append({"handler": handler.__name__, "success": False, "error": str(exc)})

        return results

    def add_middleware(self, middleware: Callable) -> None:
        """Добавить middleware для обработки событий."""
        self._middlewares.append(middleware)

    def clear(self) -> None:
        """Очистить все подписки (для тестов)."""
        self._handlers.clear()
