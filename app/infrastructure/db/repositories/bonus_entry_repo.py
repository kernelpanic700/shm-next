# =============================================================================
# shm-next — Bonus Entry Repository
# =============================================================================
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.entities.bonus_entry import BonusEntry
from app.core.domain.repositories.bonus_entry import BonusEntryRepositoryProtocol
from app.infrastructure.db.models.bonus_entry import BonusEntryModel
from app.infrastructure.db.repositories.base import BaseRepository


class BonusEntryRepository(BonusEntryRepositoryProtocol, BaseRepository):
    """Репозиторий бонусных записей."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, BonusEntryModel)

    async def get(self, entry_id: UUID) -> BonusEntry | None:
        """Получить бонусную запись по ID."""
        model = await self._session.get(BonusEntryModel, entry_id)
        return self._to_domain(model) if model else None

    async def get_by_abonent(self, abonent_id: UUID) -> list[BonusEntry]:
        """Получить бонусные записи абонента."""
        stmt = select(BonusEntryModel).where(
            BonusEntryModel.abonent_id == abonent_id
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def get_usable_by_abonent(
        self,
        abonent_id: UUID,
        at: datetime,
    ) -> list[BonusEntry]:
        """Получить активные неистёкшие бонусы абонента."""
        check_at = at.replace(tzinfo=None) if at.tzinfo is not None else at
        stmt = (
            select(BonusEntryModel)
            .where(
                BonusEntryModel.abonent_id == abonent_id,
                BonusEntryModel.is_active,
                (BonusEntryModel.expires_at.is_(None))
                | (BonusEntryModel.expires_at >= check_at),
            )
            .order_by(BonusEntryModel.expires_at.asc().nulls_last(), BonusEntryModel.id)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]

    async def get_active(self) -> list[BonusEntry]:
        """Получить все активные бонусные записи."""
        stmt = select(BonusEntryModel).where(
            BonusEntryModel.is_active
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def get_expired(self) -> list[BonusEntry]:
        """Получить истёкшие бонусные записи."""
        now = datetime.now(UTC).replace(tzinfo=None)
        stmt = select(BonusEntryModel).where(
            BonusEntryModel.expires_at < now,
            BonusEntryModel.is_active
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def save(self, entry: BonusEntry) -> BonusEntry:
        """Сохранить бонусную запись."""
        # Пытаемся найти существующую модель
        model = await self._session.get(BonusEntryModel, entry.id)

        if model:
            # Обновляем существующую модель
            model.abonent_id = entry.abonent_id
            model.amount = entry.amount.amount if entry.amount else 0.0
            model.currency = entry.amount.currency.value if entry.amount else "RUB"
            model.reason = entry.reason
            model.expires_at = entry.expires_at
            model.is_active = entry.is_active
            model.source = entry.source
            model.version = entry.version
        else:
            # Создаём новую модель
            model = BonusEntryModel(
                id=entry.id,
                abonent_id=entry.abonent_id,
                amount=entry.amount.amount if entry.amount else 0.0,
                currency=entry.amount.currency.value if entry.amount else "RUB",
                reason=entry.reason,
                expires_at=entry.expires_at,
                is_active=entry.is_active,
                source=entry.source,
                version=entry.version,
            )

        saved = await BaseRepository.save(self, model)
        return self._to_domain(saved)

    def _to_domain(self, model: BonusEntryModel) -> BonusEntry:
        """Конвертация модели в доменную сущность."""
        from app.core.domain.value_objects import Money

        return BonusEntry(
            id=model.id,
            abonent_id=model.abonent_id,
            amount=Money(model.amount, model.currency),
            reason=model.reason,
            expires_at=model.expires_at,
            is_active=model.is_active,
            source=model.source,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )
