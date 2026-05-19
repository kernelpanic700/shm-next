# =============================================================================
# shm-next — Action Executor
# =============================================================================
"""
Исполнитель внешних действий.

Выполняет действия через ActionRegistry с поддержкой:
- Retry
- Circuit breaker
- Timeout
- DLQ
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

import structlog

from app.infrastructure.external.action_registry import ActionRegistry
from app.infrastructure.external.dlq import DeadLetterQueue

logger = structlog.get_logger("action_executor")


@dataclass
class ExecutionConfig:
    """Конфигурация выполнения действия."""
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0


@dataclass
class ExecutionResult:
    """Результат выполнения действия."""
    success: bool
    result: Any = None
    error: str | None = None
    attempts: int = 1
    duration_ms: float = 0


class CircuitBreaker:
    """
    Circuit Breaker — предотвращает повторные вызовы упавшего сервиса.

    States:
    - CLOSED: Нормальная работа
    - OPEN: Сервис упал, запросы блокируются
    - HALF_OPEN: Пробуем один запрос
    """

    def __init__(self, threshold: int = 5, timeout: float = 60.0) -> None:
        self._threshold = threshold
        self._timeout = timeout
        self._failures = 0
        self._last_failure_time: float | None = None
        self._state: str = "CLOSED"

    def record_success(self) -> None:
        self._failures = 0
        self._state = "CLOSED"

    def record_failure(self) -> None:
        self._failures += 1
        self._last_failure_time = time.monotonic()
        if self._failures >= self._threshold:
            self._state = "OPEN"

    def can_execute(self) -> bool:
        if self._state == "CLOSED":
            return True
        if self._state == "OPEN":
            if (
                self._last_failure_time is not None
                and time.monotonic() - self._last_failure_time > self._timeout
            ):
                self._state = "HALF_OPEN"
                return True
            return False
        # HALF_OPEN
        return True


class ActionExecutor:
    """
    Исполнитель внешних действий.

    Обеспечивает retry, circuit breaker и интеграцию с DLQ.
    """

    def __init__(
        self,
        registry: ActionRegistry,
        dlq: DeadLetterQueue | None = None,
        config: ExecutionConfig | None = None,
    ) -> None:
        self._registry = registry
        self._dlq = dlq
        self._config = config or ExecutionConfig()
        self._circuit_breakers: dict[str, CircuitBreaker] = {}

    async def execute(
        self,
        action_name: str,
        **kwargs: Any,
    ) -> ExecutionResult:
        """
        Выполнить действие с retry и circuit breaker.

        Args:
            action_name: Имя действия
            **kwargs: Параметры действия

        Returns:
            ExecutionResult: Результат выполнения
        """
        cb = self._circuit_breakers.setdefault(
            action_name,
            CircuitBreaker(
                threshold=self._config.circuit_breaker_threshold,
                timeout=self._config.circuit_breaker_timeout,
            ),
        )

        if not cb.can_execute():
            logger.warning(
                "Circuit breaker open",
                action=action_name,
            )
            if self._dlq:
                await self._dlq.enqueue(
                    action_name=action_name,
                    payload=kwargs,
                    reason="circuit_breaker_open",
                )
            return ExecutionResult(
                success=False,
                error="Circuit breaker open",
            )

        last_error: str | None = None
        start_time = time.monotonic()

        for attempt in range(1, self._config.max_retries + 1):
            try:
                result = await self._registry.execute(action_name, **kwargs)
                duration = (time.monotonic() - start_time) * 1000

                if result["success"]:
                    cb.record_success()
                    return ExecutionResult(
                        success=True,
                        result=result.get("result"),
                        attempts=attempt,
                        duration_ms=duration,
                    )
                else:
                    last_error = result.get("error", "Unknown error")

            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "Action execution attempt failed",
                    action=action_name,
                    attempt=attempt,
                    error=last_error,
                )

            if attempt < self._config.max_retries:
                await asyncio.sleep(
                    self._config.retry_delay * attempt
                )

        # Все попытки исчерпаны
        cb.record_failure()

        if self._dlq:
            await self._dlq.enqueue(
                action_name=action_name,
                payload=kwargs,
                reason=last_error or "max_retries_exceeded",
            )

        return ExecutionResult(
            success=False,
            error=last_error,
            attempts=self._config.max_retries,
            duration_ms=(time.monotonic() - start_time) * 1000,
        )
