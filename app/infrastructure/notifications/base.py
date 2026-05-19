# =============================================================================
# shm-next — Base Notification Service
# =============================================================================
"""
Базовый класс сервиса уведомлений.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class NotificationResult:
    """Результат отправки уведомления."""
    success: bool
    message_id: str | None = None
    error: str | None = None
    extra: dict[str, Any] | None = None


class NotificationService(ABC):
    """
    Абстрактный сервис уведомлений.

    Все каналы уведомлений наследуют этот класс.
    """

    @abstractmethod
    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        **kwargs: Any,
    ) -> NotificationResult:
        """Отправить уведомление."""
        ...

    @abstractmethod
    async def send_bulk(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        **kwargs: Any,
    ) -> list[NotificationResult]:
        """Массовая отправка уведомлений."""
        ...
