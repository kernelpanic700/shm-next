# =============================================================================
# shm-next — Worker Tasks: Billing
# =============================================================================
"""Биллинговые задачи."""

from __future__ import annotations

from datetime import date

from taskiq import TaskiqDepends

from app.core.application.billing.billing_service import BillingService
from app.core.services.event_bus import EventBus
from app.infrastructure.db.unit_of_work import UnitOfWork
from app.worker.brokers import broker


async def run_billing_cycle(
    period_start: date | None = None,
    period_end: date | None = None,
    uow: UnitOfWork = TaskiqDepends(UnitOfWork),
) -> dict:
    """Запустить биллинг-цикл."""
    service = BillingService(uow=uow, event_bus=EventBus())

    async with uow:
        result = await service.run_billing_cycle(
            period_start=period_start or date.today(),
            period_end=period_end or date.today(),
        )
        await uow.commit()
        return {"status": "success", "processed": len(result)}


# Taskiq задача
run_billing_cycle_task = broker.task(run_billing_cycle)
