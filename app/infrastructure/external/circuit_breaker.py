# =============================================================================
# shm-next — Circuit Breaker
# =============================================================================
"""
Circuit Breaker — защита от каскадных сбоев.

Предотвращает отправку запросов к неработающему внешнему сервису.
Три состояния: CLOSED → OPEN → HALF_OPEN → CLOSED/OPEN.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum
from threading import Lock


class CircuitState(Enum):
    """Состояния Circuit Breaker."""
    CLOSED = "closed"       # Нормальная работа
    OPEN = "open"           # Запросы блокируются
    HALF_OPEN = "half_open" # Пробный запрос


class CircuitBreaker:
    """
    Circuit Breaker для защиты от каскадных сбоев.

    Логика:
    1. CLOSED: Запросы проходят нормально. При N ошибках → OPEN
    2. OPEN: Все запросы блокируются. Через timeout → HALF_OPEN
    3. HALF_OPEN: Один пробный запрос. Успех → CLOSED, неудача → OPEN
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = timedelta(seconds=recovery_timeout)
        self._success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: datetime | None = None
        self._lock = Lock()

    def allow_request(self) -> bool:
        """
        Проверка: разрешён ли запрос.

        Returns:
            bool: True если запрос может быть отправлен
        """
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    return True
                return False

            if self._state == CircuitState.HALF_OPEN:
                return True

            return False

    def record_success(self) -> None:
        """Фиксация успешного выполнения."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self._success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    def record_failure(self) -> None:
        """Фиксация неудачного выполнения."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now(UTC)

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
            elif (
                self._state == CircuitState.CLOSED
                and self._failure_count >= self._failure_threshold
            ):
                self._state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Проверка: прошло ли достаточно времени для повторной попытки."""
        if self._last_failure_time is None:
            return True
        return datetime.now(UTC) - self._last_failure_time >= self._recovery_timeout

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def reset(self) -> None:
        """Принудительный сброс в состояние CLOSED."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
