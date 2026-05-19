# =============================================================================
# shm-next — Webhook Repository
# =============================================================================
"""Репозиторий webhooks."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import WebhookModel


class WebhookRepository:
    """Репозиторий webhooks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, webhook_id: UUID) -> WebhookModel | None:
        """Получить webhook по ID."""
        return await self._session.get(WebhookModel, webhook_id)

    async def get_active(self) -> list[WebhookModel]:
        """Получить все активные webhooks."""
        stmt = select(WebhookModel).where(WebhookModel.is_active)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_event(self, event_type: str) -> list[WebhookModel]:
        """Получить webhooks, подписанные на событие."""
        stmt = select(WebhookModel).where(
            WebhookModel.is_active
        )
        result = await self._session.execute(stmt)
        webhooks = result.scalars().all()
        return [w for w in webhooks if event_type in (w.events or [])]

    async def save(self, webhook: WebhookModel) -> WebhookModel:
        """Сохранить webhook."""
        self._session.add(webhook)
        await self._session.flush()
        await self._session.refresh(webhook)
        return webhook

    async def delete(self, webhook_id: UUID) -> bool:
        """Удалить webhook."""
        webhook = await self._session.get(WebhookModel, webhook_id)
        if webhook:
            await self._session.delete(webhook)
            return True
        return False
