# =============================================================================
# shm-next — Health Check API
# =============================================================================
"""Эндпоинты для проверки здоровья системы."""

from __future__ import annotations

from datetime import datetime

from litestar import Controller, get

from app.infrastructure.db.unit_of_work import UnitOfWork


class HealthController(Controller):
    """Контроллер для health checks."""

    path = "/health"
    tags = ["Health"]

    @get("/", summary="Health check")
    async def health_check(self) -> dict:
        """Проверка доступности API."""
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "3.0.0",
        }

    @get("/db", summary="Database health check")
    async def db_health_check(self, uow: UnitOfWork) -> dict:
        """Проверка соединения с БД."""
        try:
            async with uow:
                await uow.session.execute("SELECT 1")
            return {"status": "ok", "database": "connected"}
        except Exception as e:
            return {"status": "error", "database": str(e)}
