# =============================================================================
# shm-next — Unit of Work
# =============================================================================
"""
Unit of Work — паттерн для управления транзакциями.

Обеспечивает:
- Единую сессию для всех репозиториев в рамках одной операции
- Атомарность изменений (commit/rollback)
- Корректное закрытие ресурсов
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.repositories.abonent_repo import AbonentRepository
from app.infrastructure.db.repositories.audit_log_repo import AuditLogRepository
from app.infrastructure.db.repositories.billing_repo import BillingRepository
from app.infrastructure.db.repositories.bonus_entry_repo import BonusEntryRepository
from app.infrastructure.db.repositories.catalog_service_repo import CatalogServiceRepository
from app.infrastructure.db.repositories.discount_repo import DiscountRepository
from app.infrastructure.db.repositories.event_action_rule_repo import EventActionRuleRepository
from app.infrastructure.db.repositories.invoice_repo import InvoiceRepository
from app.infrastructure.db.repositories.notification_repo import NotificationRepository
from app.infrastructure.db.repositories.payment_repo import PaymentRepository
from app.infrastructure.db.repositories.service_repo import ServiceRepository
from app.infrastructure.db.repositories.session_repo import SessionRepository
from app.infrastructure.db.repositories.spool_repo import SpoolTaskRepository
from app.infrastructure.db.repositories.tariff_repo import TariffRepository
from app.infrastructure.db.repositories.tariff_service_repo import TariffServiceRepository
from app.infrastructure.db.repositories.webhook_repo import WebhookRepository
from app.infrastructure.db.repositories.withdraw_repo import WithdrawRepository


class UnitOfWork:
    """
    Unit of Work — координатор транзакций.

    Все репозитории разделяют одну сессию.
    Изменения фиксируются атомарно через commit().
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._abonent_repo: AbonentRepository | None = None
        self._service_repo: ServiceRepository | None = None
        self._tariff_repo: TariffRepository | None = None
        self._payment_repo: PaymentRepository | None = None
        self._billing_repo: BillingRepository | None = None
        self._withdraw_repo: WithdrawRepository | None = None
        self._spool_repo: SpoolTaskRepository | None = None
        self._discount_repo: DiscountRepository | None = None
        self._bonus_entry_repo: BonusEntryRepository | None = None
        self._invoice_repo: InvoiceRepository | None = None
        self._session_repo: SessionRepository | None = None
        self._notification_repo: NotificationRepository | None = None
        self._webhook_repo: WebhookRepository | None = None
        self._tariff_service_repo: TariffServiceRepository | None = None
        self._audit_log_repo: AuditLogRepository | None = None
        self._catalog_service_repo: CatalogServiceRepository | None = None
        self._event_action_rule_repo: EventActionRuleRepository | None = None

    @property
    def abonents(self) -> AbonentRepository:
        if self._abonent_repo is None:
            self._abonent_repo = AbonentRepository(self._session)
        return self._abonent_repo

    @property
    def services(self) -> ServiceRepository:
        if self._service_repo is None:
            self._service_repo = ServiceRepository(self._session)
        return self._service_repo

    @property
    def tariffs(self) -> TariffRepository:
        if self._tariff_repo is None:
            self._tariff_repo = TariffRepository(self._session)
        return self._tariff_repo

    @property
    def payments(self) -> PaymentRepository:
        if self._payment_repo is None:
            self._payment_repo = PaymentRepository(self._session)
        return self._payment_repo

    @property
    def billing(self) -> BillingRepository:
        if self._billing_repo is None:
            self._billing_repo = BillingRepository(self._session)
        return self._billing_repo

    @property
    def withdraws(self) -> WithdrawRepository:
        if self._withdraw_repo is None:
            self._withdraw_repo = WithdrawRepository(self._session)
        return self._withdraw_repo

    @property
    def spool(self) -> SpoolTaskRepository:
        if self._spool_repo is None:
            self._spool_repo = SpoolTaskRepository(self._session)
        return self._spool_repo

    @property
    def discounts(self) -> DiscountRepository:
        if self._discount_repo is None:
            self._discount_repo = DiscountRepository(self._session)
        return self._discount_repo

    @property
    def bonus_entries(self) -> BonusEntryRepository:
        if self._bonus_entry_repo is None:
            self._bonus_entry_repo = BonusEntryRepository(self._session)
        return self._bonus_entry_repo

    @property
    def invoices(self) -> InvoiceRepository:
        if self._invoice_repo is None:
            self._invoice_repo = InvoiceRepository(self._session)
        return self._invoice_repo

    @property
    def sessions(self) -> SessionRepository:
        if self._session_repo is None:
            self._session_repo = SessionRepository(self._session)
        return self._session_repo

    @property
    def notifications(self) -> NotificationRepository:
        if self._notification_repo is None:
            self._notification_repo = NotificationRepository(self._session)
        return self._notification_repo

    @property
    def webhooks(self) -> WebhookRepository:
        if self._webhook_repo is None:
            self._webhook_repo = WebhookRepository(self._session)
        return self._webhook_repo

    @property
    def tariff_services(self) -> TariffServiceRepository:
        if self._tariff_service_repo is None:
            self._tariff_service_repo = TariffServiceRepository(self._session)
        return self._tariff_service_repo

    @property
    def audit_logs(self) -> AuditLogRepository:
        if self._audit_log_repo is None:
            self._audit_log_repo = AuditLogRepository(self._session)
        return self._audit_log_repo

    @property
    def catalog_services(self) -> CatalogServiceRepository:
        if self._catalog_service_repo is None:
            self._catalog_service_repo = CatalogServiceRepository(self._session)
        return self._catalog_service_repo

    @property
    def event_action_rules(self) -> EventActionRuleRepository:
        if self._event_action_rule_repo is None:
            self._event_action_rule_repo = EventActionRuleRepository(self._session)
        return self._event_action_rule_repo

    async def commit(self) -> None:
        """Фиксация всех изменений."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Откат всех изменений."""
        await self._session.rollback()

    async def close(self) -> None:
        """Закрытие сессии."""
        await self._session.close()

    async def __aenter__(self) -> UnitOfWork:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
        await self.close()


@asynccontextmanager
async def unit_of_work(session: AsyncSession) -> AsyncGenerator[UnitOfWork, None]:
    """
    Контекстный менеджер для Unit of Work.

    Автоматически коммитит или откатывает транзакцию.

    Usage:
        async with unit_of_work(session) as uow:
            abonent = await uow.abonents.get(abonent_id)
            abonent.balance += Money("100", "RUB")
            await uow.commit()
    """
    uow = UnitOfWork(session)
    try:
        yield uow
        await uow.commit()
    except Exception:
        await uow.rollback()
        raise
    finally:
        await uow.close()
