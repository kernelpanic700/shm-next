# =============================================================================
# shm-next — Worker Tasks: Notifications
# =============================================================================
"""Задачи для отправки уведомлений."""

from __future__ import annotations

import structlog
from taskiq import TaskiqDepends

from app.infrastructure.db.unit_of_work import UnitOfWork
from app.worker.brokers import broker

logger = structlog.get_logger(__name__)


async def _send_notification_stub(notification) -> bool:
    """Stub-отправка уведомления (email/SMS/webhook)."""
    # TODO: Интеграция с реальными провайдерами
    logger.info(
        "sending_notification",
        id=str(notification.id),
        type=notification.type,
        recipient=notification.recipient,
    )
    return True


async def send_pending_notifications(
    batch_size: int = 100,
    uow: UnitOfWork = TaskiqDepends(UnitOfWork),
) -> dict:
    """Отправить отложенные уведомления."""
    async with uow:
        notifications = await uow.notifications.get_pending(batch_size=batch_size)

        sent_count = 0
        failed_count = 0

        for notification in notifications:
            try:
                await _send_notification_stub(notification)
                notification.mark_sent()
                logger.info("notification_sent", id=str(notification.id))
                sent_count += 1
            except Exception as e:
                notification.mark_failed(str(e))
                logger.error("notification_failed", id=str(notification.id), error=str(e))
                failed_count += 1

            await uow.notifications.save(notification)

        await uow.commit()
        return {"status": "success", "sent": sent_count, "failed": failed_count}


# Taskiq задача
send_pending_notifications_task = broker.task(send_pending_notifications)
