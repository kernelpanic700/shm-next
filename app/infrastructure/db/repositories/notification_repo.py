# =============================================================================
# shm-next — Notification Repository
# =============================================================================
"""Репозиторий уведомлений."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import NotificationModel


class NotificationRepository:
    """Репозиторий уведомлений."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, notification_id: UUID) -> NotificationModel | None:
        """Получить уведомление по ID."""
        return await self._session.get(NotificationModel, notification_id)

    async def get_by_abonent(
        self, abonent_id: UUID, unread_only: bool = False, limit: int = 50
    ) -> list[NotificationModel]:
        """Получить уведомления абонента."""
        stmt = select(NotificationModel).where(
            NotificationModel.abonent_id == abonent_id
        )

        if unread_only:
            stmt = stmt.where(NotificationModel.sent_at.is_(None))

        stmt = stmt.order_by(NotificationModel.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_pending(self, limit: int = 100) -> list[NotificationModel]:
        """Получить уведомления ожидающие отправки."""
        stmt = select(NotificationModel).where(
            NotificationModel.sent_at.is_(None),
            NotificationModel.status == "PENDING",
        ).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def save(self, notification: NotificationModel) -> NotificationModel:
        """Сохранить уведомление."""
        self._session.add(notification)
        await self._session.flush()
        await self._session.refresh(notification)
        return notification

    async def mark_sent(self, notification_id: UUID) -> bool:
        """Отметить уведомление как отправленное."""
        notification = await self._session.get(NotificationModel, notification_id)
        if notification:
            notification.sent_at = datetime.now(UTC)
            notification.status = "SENT"
            await self._session.flush()
            return True
        return False

    async def mark_failed(self, notification_id: UUID, error: str) -> bool:
        """Отметить уведомление как неудачное."""
        notification = await self._session.get(NotificationModel, notification_id)