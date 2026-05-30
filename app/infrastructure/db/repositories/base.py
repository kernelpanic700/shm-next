# =============================================================================
# shm-next — Base Repository
# =============================================================================
"""
Базовый репозиторий с общими методами CRUD.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Базовый репозиторий с общими операциями CRUD.

    Args:
        session: Асинхронная сессия SQLAlchemy
        model: Модель SQLAlchemy
    """

    def __init__(
        self,
        session: AsyncSession,
        model: type[T],
    ) -> None:
        self._session = session
        self._model = model

    async def get(self, entity_id: Any) -> T | None:
        """Получить сущность по ID."""
        result = await self._session.get(self._model, entity_id)
        return result

    async def get_by_field(self, field_name: str, value: Any) -> T | None:
        """Получить сущность по произвольному полю."""
        stmt = select(self._model).where(
            getattr(self._model, field_name) == value
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict[str, Any] | None = None,
    ) -> list[T]:
        """Список сущностей с пагинацией."""
        stmt = select(self._model)

        if filters:
            conditions = []
            for field, value in filters.items():
                if value is not None:
                    conditions.append(
                        getattr(self._model, field) == value
                    )
            if conditions:
                stmt = stmt.where(and_(*conditions))

        if hasattr(self._model, "created_at"):
            stmt = stmt.order_by(getattr(self._model, "created_at").desc(), getattr(self._model, "id"))
        elif hasattr(self._model, "id"):
            stmt = stmt.order_by(getattr(self._model, "id"))

        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, entity: T) -> T:
        """Сохранить сущность."""
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def delete(self, entity_id: Any) -> bool:
        """Удалить сущность."""
        entity = await self._session.get(self._model, entity_id)
        if entity is None:
            return False
        await self._session.delete(entity)
        await self._session.flush()
        return True

    async def exists(self, entity_id: Any) -> bool:
        """Проверка существования."""
        entity = await self._session.get(self._model, entity_id)
        return entity is not None

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Подсчёт количества сущностей."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self._model)

        if filters:
            conditions = []
            for field, value in filters.items():
                if value is not None:
                    conditions.append(
                        getattr(self._model, field) == value
                    )
            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = await self._session.execute(stmt)
        return result.scalar()
