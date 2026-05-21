# =============================================================================
# shm-next — Dashboard API Router
# =============================================================================
"""
Роутер для получения статистики дашборда.
"""

from __future__ import annotations

from litestar import Controller, get
from litestar.di import Provide
from litestar.status_codes import HTTP_200_OK

from app.api.dependencies import provide_uow_dependency
from app.infrastructure.db.unit_of_work import UnitOfWork


class DashboardStats:
    """Статистика дашборда."""
    total_abonents: int
    active_abonents: int
    total_balance: float
    pending_payments: int
    spool_tasks: int


class DashboardController(Controller):
    """Контроллер для статистики дашборда."""
    path = "/v1/dashboard"
    tags = ["Dashboard"]
    dependencies = {
        "uow": Provide(provide_uow_dependency),
    }

    @get(
        path="/stats",
        summary="Получить статистику дашборда",
        response_model=DashboardStats,
        status_code=HTTP_200_OK,
    )
    async def get_stats(
        self,
        uow: UnitOfWork,
    ) -> DashboardStats:
        """Получить статистику дашборда."""
        from sqlalchemy import select, func

        # Get abonent stats
        result = await uow.session.execute(
            select(
                func.count().label("total"),
                func.count().filter_by(status="ACTIVE").label("active"),
            ).select_from(uow.abonents.model)
        )
        row = result.first()
        
        # Get total balance
        balance_result = await uow.session.execute(
            select(func.coalesce(func.sum(uow.abonents.model.balance), 0))
        )
        total_balance = balance_result.scalar() or 0

        # Get pending payments count
        payments_result = await uow.session.execute(
            select(func.count()).where(uow.payments.model.status == "PENDING")
        )
        pending_payments = payments_result.scalar() or 0

        # Get spool tasks count
        spool_result = await uow.session.execute(
            select(func.count()).where(uow.spool_tasks.model.status == "PENDING")
        )
        spool_tasks = spool_result.scalar() or 0

        return DashboardStats(
            total_abonents=row.total if row else 0,
            active_abonents=row.active if row else 0,
            total_balance=float(total_balance),
            pending_payments=pending_payments,
            spool_tasks=spool_tasks,
        )


router = DashboardController


router = DashboardController