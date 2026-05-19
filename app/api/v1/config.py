# =============================================================================
# shm-next — API v1: Config
# =============================================================================
"""Эндпоинты для получения конфигурации."""

from __future__ import annotations

from litestar import Controller, get
from litestar.datastructures import State

from app.api.dto.responses import ApiResponse


class ConfigController(Controller):
    path = "/v1/config"
    tags = ["Config"]

    @get(
        "/",
        summary="Конфигурация",
        description="Получить текущую конфигурацию приложения",
    )
    async def get_config(self, state: State) -> ApiResponse:
        from app.api.config import get_app_config

        config = get_app_config()
        return ApiResponse(
            success=True,
            data={
                "debug": config.debug,
                "api_host": config.api_host,
                "api_port": config.api_port,
                "cors_origins": config.cors_origins,
                "billing_cycle_day": config.billing_cycle_day,
                "billing_batch_size": config.billing_batch_size,
                "default_currency": config.default_currency,
                "rate_limits": {
                    "default": config.rate_limit_default,
                    "auth": config.rate_limit_auth,
                    "api": config.rate_limit_api,
                },
                "version": "3.0.0",
            },
        )

    @get(
        "/health",
        summary="Health Check",
        description="Проверка работоспособности сервиса",
    )
    async def health_check(self, state: State) -> ApiResponse:
        from datetime import datetime

        checks = {
            "api": "healthy",
            "timestamp": datetime.now().isoformat(),
        }

        # Проверяем подключение к БД
        try:
            from app.api.config import get_app_config
            from app.infrastructure.db.database import create_engine
            config = get_app_config()
            engine = create_engine(config.database_url)

            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = "healthy"
        except Exception as e:
            checks["database"] = f"unhealthy: {e!s}"

        # Проверяем Redis
        try:
            from redis.asyncio import Redis

            from app.api.config import get_app_config
            config = get_app_config()
            client = Redis.from_url(config.redis_url)
            await client.ping()
            await client.close()
            checks["redis"] = "healthy"
        except Exception as e:
            checks["redis"] = f"unhealthy: {e!s}"

        all_healthy = all(
            v == "healthy" for v in checks.values() if isinstance(v, str)
        )

        return ApiResponse(
            success=all_healthy,
            data={
                "status": "healthy" if all_healthy else "degraded",
                "checks": checks,
                "version": "3.0.0",
            },
        )
