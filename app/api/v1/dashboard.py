# =============================================================================
# shm-next — Dashboard API Router
# =============================================================================
"""
Роутер для получения статистики дашборда.
"""

from __future__ import annotations

from typing import Any

from litestar import Controller, get
from litestar.di import Provide
from litestar.status_codes import HTTP_200_OK

from app.api.dependencies import provide_uow_dependency


class DashboardController(Controller):
    """Контроллер для статистики дашборда."""
    path = "/dashboard"
    tags = ["Dashboard"]
    dependencies = {
        "uow": Provide(provide_uow_dependency),
    }

    @get(
        path="/stats",
        summary="Получить статистику дашборда",
        status_code=HTTP_200_OK,
    )
    async def get_stats(self, uow: Any) -> dict[str, Any]:
        """Получить статистику дашборда."""
        # Demo mode: return mock data
        return {
            "total_abonents": 1,
            "active_abonents": 1,
            "total_balance": 1000.0,
            "pending_payments": 0,
            "spool_tasks": 0,
        }


router = DashboardController
