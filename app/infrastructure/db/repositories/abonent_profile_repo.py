# =============================================================================
# shm-next - Abonent profile/storage repositories
# =============================================================================
from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.abonent import AbonentProfileModel, AbonentStorageModel
from app.infrastructure.db.repositories.base import BaseRepository


class AbonentProfileRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AbonentProfileModel)

    async def get_by_abonent(self, abonent_id: UUID) -> AbonentProfileModel | None:
        stmt = select(AbonentProfileModel).where(AbonentProfileModel.abonent_id == abonent_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(self, abonent_id: UUID, data: dict) -> AbonentProfileModel:
        model = await self.get_by_abonent(abonent_id)
        if model is None:
            model = AbonentProfileModel(abonent_id=abonent_id, data=data)
        else:
            model.data = data
        return await self.save(model)


class AbonentStorageRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AbonentStorageModel)

    async def list_by_abonent(self, abonent_id: UUID) -> list[AbonentStorageModel]:
        stmt = (
            select(AbonentStorageModel)
            .where(AbonentStorageModel.abonent_id == abonent_id)
            .order_by(AbonentStorageModel.created_at.desc(), AbonentStorageModel.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_item(self, abonent_id: UUID, name: str) -> AbonentStorageModel | None:
        stmt = select(AbonentStorageModel).where(
            AbonentStorageModel.abonent_id == abonent_id,
            AbonentStorageModel.name == name,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        abonent_id: UUID,
        name: str,
        data: dict | str,
        content_type: str = "application/json",
        user_service_id: UUID | None = None,
        settings: dict | None = None,
    ) -> AbonentStorageModel:
        model = await self.get_item(abonent_id, name)
        payload = self._pack_data(data, content_type)
        item_settings = dict(settings or {})
        if isinstance(data, dict):
            item_settings["json"] = True
            content_type = "application/json"
        if model is None:
            model = AbonentStorageModel(
                abonent_id=abonent_id,
                name=name,
                data=payload,
                content_type=content_type,
                user_service_id=user_service_id,
                settings=item_settings,
            )
        else:
            model.data = payload
            model.content_type = content_type
            model.user_service_id = user_service_id
            model.settings = item_settings
        return await self.save(model)

    async def delete_item(self, abonent_id: UUID, name: str) -> bool:
        model = await self.get_item(abonent_id, name)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    @staticmethod
    def unpack_data(model: AbonentStorageModel) -> dict | str | None:
        if model.data is None:
            return None
        text = model.data.decode("utf-8")
        if (model.settings or {}).get("json") or model.content_type == "application/json":
            return json.loads(text)
        return text

    @staticmethod
    def _pack_data(data: dict | str, content_type: str) -> bytes:
        if isinstance(data, dict) or content_type == "application/json":
            return json.dumps(data, ensure_ascii=False).encode("utf-8")
        return data.encode("utf-8")
