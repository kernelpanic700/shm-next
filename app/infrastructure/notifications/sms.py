# =============================================================================
# shm-next — SMS Notification Service
# =============================================================================
"""
Сервис отправки SMS-уведомлений.

Интеграция с SMS-провайдерами через REST API.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.api.config import AppConfig
from app.infrastructure.notifications.base import NotificationResult, NotificationService

logger = structlog.get_logger("sms")


class SMSService(NotificationService):
    """
    Сервис отправки SMS.

    Поддерживает подключение различных SMS-провайдеров.
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        self._config = config or AppConfig()

    async def send(
        self,
        recipient: str,
        subject: str | None = None,
        body: str = "",
        **kwargs: Any,
    ) -> NotificationResult:
        """
        Отправить SMS.

        Args:
            recipient: Номер телефона
            body: Текст сообщения

        Returns:
            NotificationResult: Результат отправки
        """
        try:
            if not self._config.sms_api_url:
                logger.warning(
                    "SMS API URL not configured, simulating send",
                    phone=recipient,
                )
                return NotificationResult(
                    success=True,
                    message_id=f"sms-sim-{hash(recipient + body)}",
                )

            # Формируем запрос к SMS-провайдеру
            payload = {
                "to": recipient,
                "message": body,
                "sender": self._config.sms_sender,
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._config.sms_api_key}",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self._config.sms_api_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

                data = response.json()
                message_id = data.get("message_id", data.get("id"))

                logger.info(
                    "SMS sent",
                    phone=recipient,
                    message_id=message_id,
                )

                return NotificationResult(
                    success=True,
                    message_id=str(message_id),
                )

        except httpx.HTTPStatusError as exc:
            logger.error(
                "SMS API error",
                phone=recipient,
                status_code=exc.response.status_code,
                error=str(exc),
            )
            return NotificationResult(
                success=False,
                error=f"SMS API error: {exc.response.status_code}",
            )
        except Exception as exc:
            logger.error(
                "SMS send failed",
                phone=recipient,
                error=str(exc),
            )
            return NotificationResult(
                success=False,
                error=str(exc),
            )

    async def send_bulk(
        self,
        recipients: list[str],
        subject: str | None = None,
        body: str = "",
        **kwargs: Any,
    ) -> list[NotificationResult]:
        """Массовая отправка SMS."""
        results = []
        for recipient in recipients:
            result = await self.send(recipient, body=body, **kwargs)
            results.append(result)
        return results
