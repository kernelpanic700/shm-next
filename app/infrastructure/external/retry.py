# =============================================================================
# shm-next — Retry Policy
# =============================================================================
"""
Политика повторных попыток с экспоненциальным backoff.

Используется ActionExecutor для повтора неудачных внешних действий.
"""

from __future__ import annotations

from datetime import timedelta


class RetryPolicy:
    """
    Политика повторных попыток с экспоненциальным backoff.

    Формула задержки: base_delay * (multiplier ^ attempt) + jitter
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 300.0,
        multiplier: float = 2.0,
        max_attempts: int = 5,
        jitter: bool = True,
    ) -> None:
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._multiplier = multiplier
        self._max_attempts = max_attempts
        self._jitter = jitter

    def get_delay(self, attempt: int) -> timedelta:
        """
        Вычисление задержки перед следующей попыткой.

        Args:
            attempt: Номер попытки (0-based)

        Returns:
            timedelta: Время ожидания перед повтором
        """
        import random

        delay = self._base_delay * (self._multiplier ** attempt)
        delay = min(delay, self._max_delay)

        if self._jitter:
            delay = delay * (0.5 + random.random())

        return timedelta(seconds=delay)

    def should_retry(self, attempt: int) -> bool:
        """Проверка: нужно ли повторять попытку."""
        return attempt < self._max_attempts


class RetryPolicyBuilder:
    """Builder для создания RetryPolicy."""

    def __init__(self) -> None:
        self._base_delay = 1.0
        self._max_delay = 300.0
        self._multiplier = 2.0
        self._max_attempts = 5
        self._jitter = True

    def with_base_delay(self, delay: float) -> RetryPolicyBuilder:
        self._base_delay = delay
        return self

    def with_max_delay(self, delay: float) -> RetryPolicyBuilder:
        self._max_delay = delay
        return self

    def with_multiplier(self, multiplier: float) -> RetryPolicyBuilder:
        self._multiplier = multiplier
        return self

    def with_max_attempts(self, attempts: int) -> RetryPolicyBuilder:
        self._max_attempts = attempts
        return self

    def with_jitter(self, enabled: bool) -> RetryPolicyBuilder:
        self._jitter = enabled
        return self

    def build(self) -> RetryPolicy:
        return RetryPolicy(
            base_delay=self._base_delay,
            max_delay=self._max_delay,
            multiplier=self._multiplier,
            max_attempts=self._max_attempts,
            jitter=self._jitter,
        )
