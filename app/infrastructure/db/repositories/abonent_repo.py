# =============================================================================
# shm-next — Abonent Repository
# =============================================================================
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.entities.abonent import Abonent
from app.core.domain.repositories.abonent import AbonentRepositoryProtocol
from app.infrastructure.db.models.abonent import AbonentModel
from app.infrastructure.db.repositories.base import BaseRepository


class AbonentRepository(AbonentRepositoryProtocol, BaseRepository):
    """Репозиторий абонентов."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AbonentModel)

    async def get(self, abonent_id: UUID) -> Abonent | None:
        """Получить абонента по ID."""
        model = await self._session.get(AbonentModel, abonent_id)
        return self._to_domain(model) if model else None

    async def get_by_phone(self, phone: str) -> Abonent | None:
        """Получить абонента по телефону."""
        model = await self.get_by_field("phone", phone)
        return self._to_domain(model) if model else None

    async def get_by_account(self, account_number: str) -> Abonent | None:
        """Получить абонента по номеру лицевого счёта."""
        stmt = select(AbonentModel).where(
            AbonentModel.account_number == account_number
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list(
        self,
        offset: int = 0,
        limit: int = 50,
        status: str | None = None,
    ) -> list[Abonent]:
        """Список абонентов с пагинацией."""
        filters = {"status": status} if status else {}
        models = await BaseRepository.list(self, offset=offset, limit=limit, filters=filters)
        return [self._to_domain(m) for m in models]

    async def list_active(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Abonent]:
        """Список активных абонентов для биллинг-цикла."""
        stmt = (
            select(AbonentModel)
            .where(AbonentModel.status == "ACTIVE")
            .order_by(AbonentModel.id)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]

    async def save(self, abonent: Abonent) -> Abonent:
        """Сохранить абонента."""
        # Пытаемся найти существующую модель
        model = await self._session.get(AbonentModel, abonent.id)

        if model:
            # Обновляем существующую модель
            model.full_name = abonent.full_name
            model.phone = abonent.phone
            model.email = abonent.email
            model.account_number = abonent.account_number
            model.balance = float(abonent.balance.amount)
            model.currency = abonent.balance.currency.value if hasattr(abonent.balance, 'currency') else "RUB"
            model.status = abonent.status.value
            model.allow_negative = abonent.allow_negative
            model.tariff_id = abonent.tariff_id
            model.password_hash = abonent.password_hash
            model.version = abonent.version
        else:
            # Создаём новую модель
            model = AbonentModel(
                id=abonent.id,
                full_name=abonent.full_name,
                phone=abonent.phone,
                email=abonent.email,
                account_number=abonent.account_number,
                balance=float(abonent.balance.amount),
                currency=abonent.balance.currency.value if hasattr(abonent.balance, 'currency') else "RUB",
                status=abonent.status.value,
                allow_negative=abonent.allow_negative,
                tariff_id=abonent.tariff_id,
                password_hash=abonent.password_hash,
                version=abonent.version,
            )

        saved = await BaseRepository.save(self, model)
        return self._to_domain(saved)

    async def delete(self, abonent_id: UUID) -> bool:
        """Удалить абонента."""
        return await BaseRepository.delete(self, abonent_id)

    async def exists(self, abonent_id: UUID) -> bool:
        """Проверка существования абонента."""
        return await BaseRepository.exists(self, abonent_id)

    def _to_domain(self, model: AbonentModel) -> Abonent:
        """Конвертация модели в доменную сущность."""
        from app.core.domain.value_objects import AbonentStatus, Money

        return Abonent(
            id=model.id,
            full_name=model.full_name,
            phone=model.phone,
            email=model.email,
            account_number=model.account_number,
            balance=Money(model.balance, model.currency),
            status=AbonentStatus(model.status),
            allow_negative=model.allow_negative,
            tariff_id=model.tariff_id,
            password_hash=model.password_hash,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )
