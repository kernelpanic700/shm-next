# =============================================================================
# shm-next — Action Registry
# =============================================================================
"""
Реестр внешних действий.

Позволяет регистрировать и вызывать внешние действия
(NAS-команды, webhook-вызовы, уведомления и т.д.)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import structlog

logger = structlog.get_logger("action_registry")


class ActionRegistry:
    """
    Реестр внешних действий.

    Действия регистрируются по имени и вызываются через execute().
    Поддерживается как синхронные, так и асинхронные обработчики.
    """

    def __init__(self) -> None:
        self._actions: dict[str, Callable] = {}

    def register(
        self,
        name: str,
        handler: Callable[..., Any | Awaitable[Any]],
    ) -> None:
        """
        Зарегистрировать действие.

        Args:
            name: Имя действия
            handler: Функция-обработчик
        """
        if name in self._actions:
            logger.warning(
                "Action already registered, overwriting",
                action=name,
            )
        self._actions[name] = handler
        logger.info("Action registered", action=name)

    def unregister(self, name: str) -> bool:
        """Удалить действие из реестра."""
        if name in self._actions:
            del self._actions[name]
            return True
        return False

    async def execute(
        self,
        name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Выполнить зарегистрированное действие.

        Args:
            name: Имя действия
            **kwargs: Параметры действия

        Returns:
            dict: Результат выполнения

        Raises:
            ValueError: Если действие не найдено
        """
        if name not in self._actions:
            raise ValueError(f"Unknown action: {name}")

        handler = self._actions[name]

        try:
            result = handler(**kwargs)
            if hasattr(result, "__await__"):
                result = await result
            return {"success": True, "result": result}
        except Exception as exc:
            logger.error(
                "Action execution failed",
                action=name,
                error=str(exc),
            )
            return {"success": False, "error": str(exc)}

    def list_actions(self) -> list[str]:
        """Получить список зарегистрированных действий."""
        return list(self._actions.keys())
