# =============================================================================
# shm-next — Worker Tasks: Billing
# =============================================================================
"""Биллинговые задачи."""

from __future__ import annotations

from datetime import UTC, date, datetime

from app.core.application.billing.billing_service import BillingService
from app.core.application.events import ServiceEventSpoolHandler
from app.core.application.services.service_service import ServiceService
from app.core.services.event_bus import EventBus
from app.infrastructure.db.database import create_engine, create_session_factory
from app.infrastructure.db.unit_of_work import UnitOfWork
from app.worker.brokers import broker


async def run_billing_cycle(
    period_start: date | None = None,
    period_end: date | None = None,
    offset: int = 0,
    limit: int = 100,
    uow: UnitOfWork | None = None,
) -> dict:
    """Запустить биллинг-цикл."""
    today = datetime.now(UTC).date()
    start = period_start or today
    end = period_end or today

    if uow is not None:
        async with uow:
            service = BillingService(
                uow.abonents,
                uow.billing,
                uow.services,
                uow.withdraws,
                EventBus(),
                invoice_repo=uow.invoices,
                bonus_entry_repo=uow.bonus_entries,
            )
            result = await service.run_billing_cycle(
                period_start=start,
                period_end=end,
                offset=offset,
                limit=limit,
            )
            return {"status": "success", **result}

    from app.api.config import AppConfig

    config = AppConfig()
    engine = create_engine(config.database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            async with UnitOfWork(session) as managed_uow:
                service = BillingService(
                    managed_uow.abonents,
                    managed_uow.billing,
                    managed_uow.services,
                    managed_uow.withdraws,
                    EventBus(),
                    invoice_repo=managed_uow.invoices,
                    bonus_entry_repo=managed_uow.bonus_entries,
                )
                result = await service.run_billing_cycle(
                    period_start=start,
                    period_end=end,
                    offset=offset,
                    limit=limit,
                )
                return {"status": "success", **result}
    finally:
        await engine.dispose()


def _build_shm_service_service(uow: UnitOfWork) -> ServiceService:
    event_bus = EventBus()
    spool_handler = ServiceEventSpoolHandler(
        rule_repo=uow.event_action_rules,
        spool_repo=uow.spool,
    )
    for event_type in ServiceEventSpoolHandler.SUPPORTED_EVENTS:
        event_bus.subscribe(event_type, spool_handler)
    return ServiceService(
        uow.services,
        event_bus,
        catalog_service_repo=uow.catalog_services,
    )


async def run_shm_auto_renewal(
    limit: int = 100,
    uow: UnitOfWork | None = None,
) -> dict:
    """Автоматически продлить истёкшие SHM-услуги с auto_bill."""
    if uow is not None:
        async with uow:
            service = _build_shm_service_service(uow)
            result = await service.renew_due_catalog_services(
                now=datetime.now(UTC),
                limit=limit,
            )
            return {"status": "success", **result}

    from app.api.config import AppConfig

    config = AppConfig()
    engine = create_engine(config.database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            async with UnitOfWork(session) as managed_uow:
                service = _build_shm_service_service(managed_uow)
                result = await service.renew_due_catalog_services(
                    now=datetime.now(UTC),
                    limit=limit,
                )
                return {"status": "success", **result}
    finally:
        await engine.dispose()


async def mark_overdue_invoices(
    limit: int = 100,
    uow: UnitOfWork | None = None,
) -> dict:
    """Перевести неоплаченные счета с истёкшим due_date в OVERDUE."""
    now = datetime.now(UTC)
    if uow is not None:
        async with uow:
            invoices = await uow.invoices.get_due_for_overdue(now=now, limit=limit)
            for invoice in invoices:
                invoice.mark_overdue()
                await uow.invoices.save(invoice)
            return {"status": "success", "marked_overdue": len(invoices)}

    from app.api.config import AppConfig

    config = AppConfig()
    engine = create_engine(config.database_url)
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            async with UnitOfWork(session) as managed_uow:
                invoices = await managed_uow.invoices.get_due_for_overdue(
                    now=now,
                    limit=limit,
                )
                for invoice in invoices:
                    invoice.mark_overdue()
                    await managed_uow.invoices.save(invoice)
                return {"status": "success", "marked_overdue": len(invoices)}
    finally:
        await engine.dispose()


# Taskiq задача
run_billing_cycle_task = broker.task(run_billing_cycle, crontab="0 2 * * *")  # Каждый день в 2:00
run_shm_auto_renewal_task = broker.task(run_shm_auto_renewal, crontab="*/10 * * * *")
mark_overdue_invoices_task = broker.task(mark_overdue_invoices, crontab="*/15 * * * *")
