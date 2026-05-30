# =============================================================================
# shm-next - Automation Repositories
# =============================================================================
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import (
    CommandTemplateModel,
    ServerGroupModel,
    ServerModel,
    SSHKeyModel,
)
from app.infrastructure.db.repositories.base import BaseRepository


class AutomationRepository(BaseRepository):
    """Small typed CRUD repository for automation configuration tables."""

    def __init__(self, session: AsyncSession, model: type[Any]) -> None:
        super().__init__(session, model)

    async def list_active(self, limit: int = 100) -> list[Any]:
        stmt = select(self._model).where(self._model.is_active.is_(True)).limit(limit)
        if hasattr(self._model, "name"):
            stmt = stmt.order_by(self._model.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete(self, entity_id: UUID) -> bool:
        model = await self._session.get(self._model, entity_id)
        if model is None:
            return False
        model.is_active = False
        model.version = (model.version or 0) + 1
        await self._session.flush()
        return True


class SSHKeyRepository(AutomationRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SSHKeyModel)


class ServerGroupRepository(AutomationRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ServerGroupModel)


class ServerRepository(AutomationRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ServerModel)

    async def list_by_group(self, group_id: UUID, active_only: bool = True) -> list[ServerModel]:
        stmt = select(ServerModel).where(ServerModel.group_id == group_id)
        if active_only:
            stmt = stmt.where(ServerModel.is_active.is_(True))
        stmt = stmt.order_by(ServerModel.name, ServerModel.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class CommandTemplateRepository(AutomationRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CommandTemplateModel)
