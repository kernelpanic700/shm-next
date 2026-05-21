# =============================================================================
# shm-next — Root Router
# =============================================================================
"""
Корневой роутер приложения.

Все эндпоинты v1 монтируются через этот роутер.
"""

from __future__ import annotations

from litestar import Router

from app.api.v1 import abonents, auth, billing, dashboard, events, invoices, payments, services, spool, tariffs, webhooks


def create_router(config=None) -> Router:
    """
    Создание корневого роутера приложения.

    Args:
        config: Конфигурация приложения (опционально)

    Returns:
        Router: Корневой роутер со всеми эндпоинтами
    """
    return Router(
        path="/api",
        tags=["API"],
        route_handlers=[
            # === API v1 ===
            abonents.router,
            tariffs.router,
            services.router,
            billing.router,
            payments.router,
            auth.router,
            spool.router,
            events.router,
            config.router,
            invoices.router,
            webhooks.router,
            dashboard.router,
        ],
    )
