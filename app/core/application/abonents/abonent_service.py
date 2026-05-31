# =============================================================================
# shm-next — Abonent Application Service
# =============================================================================
"""
Application Service для работы с абонентами.

Координирует бизнес-логику между доменными сущностями и инфраструктурой.
"""

from __future__ import annotations

from uuid import UUID

import structlog

from app.core.domain.entities.abonent import (
    Abonent,
    AbonentCreate,
    AbonentUpdate,
)
from app.core.domain.repositories.abonent import AbonentRepositoryProtocol
from app.core.domain.value_objects import AbonentStatus, Money
from app.core.services.event_bus import EventBus

logger = structlog.get_logger("abonent_service")


class AbonentService:
    """
    Сервис работы с абонентами.

    Use Cases:
    - Создание абонента
    - Получение информации
    - Обновление данных
    - Управление балансом
    - Удаление
    """

    def __init__(
        self,
        abonent_repo: AbonentRepositoryProtocol,
        event_bus: EventBus,
    ) -> None:
        self._abonent_repo = abonent_repo
        self._event_bus = event_bus

    async def create_abonent(self, data: AbonentCreate) -> Abonent:
        """
        Создать нового абонента.

        Args:
            data: Данные для создания абонента

        Returns:
            Abonent: Созданный абонент

        Raises:
            ValueError: Если абонент с таким телефоном уже существует
        """
        # Проверяем уникальность телефона
        existing = await self._abonent_repo.get_by_phone(data.phone)
        if existing is not None:
            raise ValueError(
                f"Abonent with phone {data.phone} already exists"
            )

        # Проверяем уникальность номера лицевого счёта
        if data.account_number:
            existing_account = await self._abonent_repo.get_by_account(
                data.account_number
            )
            if existing_account is not None:
                raise ValueError(
                    f"Abonent with account {data.account_number} already exists"
                )

        # Создаём доменную сущность

        balance = Money(data.balance, data.currency)
        abonent = Abonent(
            full_name=data.full_name,
            phone=data.phone,
            login=data.login or data.phone,
            login2=data.login2 or data.email,
            email=data.email,
            account_number=data.account_number,
            balance=balance,
            allow_negative=data.allow_negative,
            tariff_id=data.tariff_id,
            partner_id=data.partner_id,
            discount=data.discount,
            credit=data.credit,
            bonus=data.bonus,
            comment=data.comment,
            contract=data.contract or data.account_number,
            can_overdraft=data.can_overdraft,
            verified=data.verified,
            settings=data._meta,
        )

        # Сохраняем в БД
        saved = await self._abonent_repo.save(abonent)

        # Публикуем событие
        from app.core.domain.events.abonent_events import AbonentCreatedEvent

        event = AbonentCreatedEvent(
            abonent_id=str(saved.id),
            full_name=saved.full_name,
            phone=saved.phone,
            account_number=saved.account_number,
            balance=float(saved.balance.amount),
            currency=saved.balance.currency.value
            if hasattr(saved.balance, "currency")
            else "RUB",
            tariff_id=str(saved.tariff_id) if saved.tariff_id else None,
        )
        await self._event_bus.publish(event)

        logger.info(
            "Abonent created",
            abonent_id=saved.id,
            phone=saved.phone,
        )

        return saved

    async def get_abonent(self, abonent_id: UUID) -> Abonent | None:
        """Получить абонента по ID."""
        return await self._abonent_repo.get(abonent_id)

    async def get_abonent_by_phone(self, phone: str) -> Abonent | None:
        """Получить абонента по телефону."""
        return await self._abonent_repo.get_by_phone(phone)

    async def get_abonent_by_account(self, account_number: str) -> Abonent | None:
        """Получить абонента по номеру лицевого счёта."""
        return await self._abonent_repo.get_by_account(account_number)

    async def list_abonents(
        self,
        offset: int = 0,
        limit: int = 50,
        status: str | None = None,
        tariff_id: UUID | None = None,
        min_balance: float | None = None,
        max_balance: float | None = None,
    ) -> list[Abonent]:
        """Список абонентов с пагинацией."""
        abonents = await self._abonent_repo.list(
            offset=offset,
            limit=limit,
            status=status,
        )
        if tariff_id is not None:
            abonents = [abonent for abonent in abonents if abonent.tariff_id == tariff_id]
        if min_balance is not None:
            abonents = [
                abonent
                for abonent in abonents
                if float(abonent.balance.amount) >= min_balance
            ]
        if max_balance is not None:
            abonents = [
                abonent
                for abonent in abonents
                if float(abonent.balance.amount) <= max_balance
            ]
        return abonents

    async def update_abonent(
        self,
        abonent_id: UUID,
        data: AbonentUpdate,
    ) -> Abonent | None:
        """
        Обновить данные абонента.

        Args:
            abonent_id: ID абонента
            data: Данные для обновления

        Returns:
            Abonent | None: Обновлённый абонент или None если не найден
        """
        abonent = await self._abonent_repo.get(abonent_id)

        if abonent is None:
            return None

        # Применяем изменения
        changes = {}

        if data.full_name is not None:
            abonent._full_name = data.full_name
            changes["full_name"] = data.full_name

        if data.phone is not None:
            # Проверяем уникальность нового телефона
            existing = await self._abonent_repo.get_by_phone(data.phone)
            if existing and existing.id != abonent_id:
                raise ValueError(
                    f"Phone {data.phone} already belongs to another abonent"
                )
            abonent._phone = data.phone
            changes["phone"] = data.phone

        if data.account_number is not None:
            existing = await self._abonent_repo.get_by_account(data.account_number)
            if existing and existing.id != abonent_id:
                raise ValueError(
                    f"Account {data.account_number} already belongs to another abonent"
                )
            abonent._account_number = data.account_number
            changes["account_number"] = data.account_number

        for attr in (
            "email",
            "login",
            "login2",
            "partner_id",
            "discount",
            "credit",
            "bonus",
            "comment",
            "contract",
            "can_overdraft",
            "verified",
        ):
            value = getattr(data, attr)
            if value is not None:
                setattr(abonent, f"_{attr}", value)
                changes[attr] = str(value) if attr == "partner_id" else value

        if data.status is not None:
            new_status = AbonentStatus(data.status)
            abonent._status = new_status
            changes["status"] = data.status

        if data.tariff_id is not None:
            abonent.assign_tariff(data.tariff_id)
            changes["tariff_id"] = str(data.tariff_id)

        if data.allow_negative is not None:
            abonent._allow_negative = data.allow_negative
            changes["allow_negative"] = data.allow_negative

        if data._meta is not None:
            abonent._settings = data._meta
            changes["settings"] = data._meta

        # Сохраняем
        saved = await self._abonent_repo.save(abonent)

        # Публикуем событие
        from app.core.domain.events.abonent_events import AbonentUpdatedEvent

        event = AbonentUpdatedEvent(
            abonent_id=str(saved.id),
            changes=changes,
        )
        await self._event_bus.publish(event)

        logger.info(
            "Abonent updated",
            abonent_id=saved.id,
            changes=changes,
        )

        return saved

    async def delete_abonent(self, abonent_id: UUID) -> bool:
        """Удалить абонента."""
        result = await self._abonent_repo.delete(abonent_id)

        if result:
            logger.info("Abonent deleted", abonent_id=abonent_id)

        return result

    async def deactivate_abonent(self, abonent_id: UUID) -> Abonent | None:
        """Мягко деактивировать абонента."""
        abonent = await self._abonent_repo.get(abonent_id)
        if abonent is None:
            return None

        abonent._status = AbonentStatus.INACTIVE
        saved = await self._abonent_repo.save(abonent)

        from app.core.domain.events.abonent_events import AbonentUpdatedEvent

        event = AbonentUpdatedEvent(
            abonent_id=str(saved.id),
            changes={"status": AbonentStatus.INACTIVE.value},
        )
        await self._event_bus.publish(event)

        logger.info("Abonent deactivated", abonent_id=saved.id)
        return saved

    async def change_balance(
        self,
        abonent_id: UUID,
        amount: float,
        currency: str = "RUB",
        reason: str = "",
    ) -> Abonent:
        """
        Изменить баланс абонента.

        Args:
            abonent_id: ID абонента
            amount: Сумма изменения (может быть отрицательной)
            currency: Валюта
            reason: Причина изменения

        Returns:
            Abonent: Абонент с обновлённым балансом

        Raises:
            ValueError: Если баланс станет отрицательным
        """
        abonent = await self._abonent_repo.get(abonent_id)

        if abonent is None:
            raise ValueError(f"Abonent {abonent_id} not found")

        old_balance = abonent.balance.amount

        abonent.change_balance(Money(amount, currency), reason=reason)

        saved = await self._abonent_repo.save(abonent)

        # Публикуем событие
        from app.core.domain.events.billing_events import BalanceChangedEvent

        event = BalanceChangedEvent(
            abonent_id=str(saved.id),
            old_balance=old_balance,
            new_balance=float(saved.balance.amount),
            currency=currency,
            reason=reason,
        )
        await self._event_bus.publish(event)

        logger.info(
            "Balance changed",
            abonent_id=saved.id,
            old_balance=old_balance,
            new_balance=float(saved.balance.amount),
        )

        return saved
