# =============================================================================
# shm-next — Abonent Repository
# =============================================================================
from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.entities.abonent import Abonent
from app.core.domain.repositories.abonent import AbonentRepositoryProtocol
from app.infrastructure.db.models.abonent import (
    AbonentModel,
    AbonentProfileModel,
    AbonentStorageModel,
)
from app.infrastructure.db.models.invoice import InvoiceModel
from app.infrastructure.db.models.notification import NotificationModel
from app.infrastructure.db.models.payment import PaymentModel
from app.infrastructure.db.models.service import ServiceModel
from app.infrastructure.db.models.session import SessionModel
from app.infrastructure.db.models.withdraw import WithdrawModel
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
            model.login = abonent.login
            model.login2 = abonent.login2
            model.email = abonent.email
            model.account_number = abonent.account_number
            model.balance = float(abonent.balance.amount)
            model.currency = abonent.balance.currency.value if hasattr(abonent.balance, 'currency') else "RUB"
            model.status = abonent.status.value
            model.allow_negative = abonent.allow_negative
            model.tariff_id = abonent.tariff_id
            model.partner_id = abonent.partner_id
            model.discount = abonent.discount
            model.credit = abonent.credit
            model.bonus = abonent.bonus
            model.comment = abonent.comment
            model.contract = abonent.contract
            model.can_overdraft = abonent.can_overdraft
            model.verified = abonent.verified
            model.settings = abonent.settings
            model.password_hash = abonent.password_hash
            model.version = abonent.version
        else:
            # Создаём новую модель
            model = AbonentModel(
                id=abonent.id,
                full_name=abonent.full_name,
                phone=abonent.phone,
                login=abonent.login,
                login2=abonent.login2,
                email=abonent.email,
                account_number=abonent.account_number,
                balance=float(abonent.balance.amount),
                currency=abonent.balance.currency.value if hasattr(abonent.balance, 'currency') else "RUB",
                status=abonent.status.value,
                allow_negative=abonent.allow_negative,
                tariff_id=abonent.tariff_id,
                partner_id=abonent.partner_id,
                discount=abonent.discount,
                credit=abonent.credit,
                bonus=abonent.bonus,
                comment=abonent.comment,
                contract=abonent.contract,
                can_overdraft=abonent.can_overdraft,
                verified=abonent.verified,
                settings=abonent.settings,
                password_hash=abonent.password_hash,
                version=abonent.version,
            )

        saved = await BaseRepository.save(self, model)
        return self._to_domain(saved)

    async def delete(self, abonent_id: UUID) -> bool:
        """Удалить абонента."""
        return await BaseRepository.delete(self, abonent_id)

    async def delete_inactive(self, abonent_id: UUID) -> bool:
        """Физически удалить неактивного абонента без расчетной истории."""
        model = await self._session.get(AbonentModel, abonent_id)
        if model is None:
            return False
        if model.status != "INACTIVE":
            raise ValueError("Only inactive abonents can be deleted")

        blockers = {
            "services": await self._count(ServiceModel, ServiceModel.abonent_id == abonent_id),
            "payments": await self._count(PaymentModel, PaymentModel.abonent_id == abonent_id),
            "withdraws": await self._count(WithdrawModel, WithdrawModel.abonent_id == str(abonent_id)),
            "invoices": await self._count(InvoiceModel, InvoiceModel.abonent_id == abonent_id),
            "notifications": await self._count(NotificationModel, NotificationModel.abonent_id == abonent_id),
            "partners": await self._count(AbonentModel, AbonentModel.partner_id == abonent_id),
        }
        blockers = {name: count for name, count in blockers.items() if count}
        if blockers:
            details = ", ".join(f"{name}={count}" for name, count in blockers.items())
            raise ValueError(f"Cannot delete inactive abonent with related records: {details}")

        await self._delete_if_table_exists(
            SessionModel,
            SessionModel.abonent_id == abonent_id,
        )
        await self._delete_if_table_exists(
            AbonentStorageModel,
            AbonentStorageModel.abonent_id == abonent_id,
        )
        await self._delete_if_table_exists(
            AbonentProfileModel,
            AbonentProfileModel.abonent_id == abonent_id,
        )
        await self._session.execute(
            sa_delete(AbonentModel).where(AbonentModel.id == abonent_id)
        )
        await self._session.flush()
        return True

    async def exists(self, abonent_id: UUID) -> bool:
        """Проверка существования абонента."""
        return await BaseRepository.exists(self, abonent_id)

    async def _count(self, model: type, condition) -> int:
        if not await self._table_exists(model):
            return 0
        stmt = select(func.count()).select_from(model).where(condition)
        result = await self._session.execute(stmt)
        return int(result.scalar() or 0)

    async def _delete_if_table_exists(self, model: type, condition) -> None:
        if not await self._table_exists(model):
            return
        await self._session.execute(sa_delete(model).where(condition))

    async def _table_exists(self, model: type) -> bool:
        table_name = getattr(model, "__tablename__", "")
        if not table_name:
            return False
        result = await self._session.execute(select(func.to_regclass(table_name)))
        return result.scalar() is not None

    def _to_domain(self, model: AbonentModel) -> Abonent:
        """Конвертация модели в доменную сущность."""
        from app.core.domain.value_objects import AbonentStatus, Money

        return Abonent(
            id=model.id,
            full_name=model.full_name,
            phone=model.phone,
            login=model.login,
            login2=model.login2,
            email=model.email,
            account_number=model.account_number,
            balance=Money(model.balance, model.currency),
            status=AbonentStatus(model.status),
            allow_negative=model.allow_negative,
            tariff_id=model.tariff_id,
            partner_id=model.partner_id,
            discount=float(model.discount or 0),
            credit=float(model.credit or 0),
            bonus=float(model.bonus or 0),
            comment=model.comment,
            contract=model.contract,
            can_overdraft=model.can_overdraft,
            verified=model.verified,
            settings=model.settings or {},
            password_hash=model.password_hash,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )
