# =============================================================================
# shm-next — Notification Service
# =============================================================================
"""Сервис для отправки уведомлений."""

from __future__ import annotations

from typing import Any

import structlog

from app.infrastructure.db.unit_of_work import UnitOfWork

logger = structlog.get_logger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений различными каналами."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def send(self, notification: Any) -> bool:
        """Отправить уведомление через выбранный канал."""
        try:
            # Выбор провайдера по channel/типу
            channel = getattr(notification, "channel", notification.type)

            match channel:
                case "email":
                    await self._send_email(notification)
                case "sms":
                    await self._send_sms(notification)
                case "push":
                    await self._send_push(notification)
                case _:
                    raise ValueError(f"Unknown notification channel: {channel}")

            # Обновление статуса
            async with self.uow:
                notification.mark_sent()
                await self.uow.notifications.save(notification)
                await self.uow.commit()

            logger.info("notification_sent", id=str(notification.id), channel=channel)
            return True

        except Exception as e:
            async with self.uow:
                notification.mark_failed(str(e))
                await self.uow.notifications.save(notification)
                await self.uow.commit()

            logger.error("notification_failed", id=str(notification.id), error=str(e))
            raise

    async def _send_email(self, notification: Any) -> None:
        """Отправка email."""
        # TODO: Интеграция с SMTP/SES
        logger.info("email_sent", to=notification.recipient, subject=getattr(notification, "subject", ""))

    async def _send_sms(self, notification: Any) -> None:
        """Отправка SMS."""
        # TODO: Интеграция с Twilio/SMS-центром
        logger.info("sms_sent", to=notification.recipient, body=getattr(notification, "body", ""))

    async def _send_push(self, notification: Any) -> None:
        """Отправка push-уведомления."""
        # TODO: Интеграция с Firebase/APNs
        logger.info("push_sent", device=notification.recipient, title=getattr(notification, "title", ""))
