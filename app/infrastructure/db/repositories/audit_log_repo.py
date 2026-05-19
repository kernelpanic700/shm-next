# =============================================================================
# shm-next — AuditLog Repository
# =============================================================================
"""Репозиторий ауди-логов."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import AuditLogModel


class AuditLogRepository:
    """Репозиторий ауди-логов."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, log_id: int) -> AuditLogModel | None:
        """Получить запись ауди-лога по ID."""
        return await self._session.get(AuditLogModel, log_id)

    async def get_by_actor(
        self, actor_id: UUID, limit: int = 50
    ) -> list[AuditLogModel]:
        """Получить записи ауди-лога по актору."""
        stmt = select(AuditLogModel).where(
            AuditLogModel.actor_id == actor_id
        ).order_by(AuditLogModel.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_resource(
        self, resource_type: str, resource_id: str, limit: int = 50
    ) -> list[AuditLogModel]:
        """Получить записи ауди-лога по ресурсу."""
        stmt = select(AuditLogModel).where(
            AuditLogModel.resource_type == resource_type,
            AuditLogModel.resource_id == resource_id,
        ).order_by(AuditLogModel.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def log(
        self,
        actor_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: str,
        old_values: dict | None = None,
        new_values: dict | None = None,
        metadata: dict | None = None,
    ) -> AuditLogModel:
        """Создать запись ауди-лога."""
        entry = AuditLogModel(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata,
        )
        self._session.add(entry)
        await self._session.flush()
        await self._session.refresh(entry)
        return entry
