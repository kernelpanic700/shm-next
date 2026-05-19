# =============================================================================
# shm-next — API v1 Router
# =============================================================================
"""
Корневой роутер API v1.

Регистрирует все контроллеры в едином пространстве имён /api/v1.
"""

from litestar import Router

from app.api.v1.abonents import AbonentController
from app.api.v1.auth import AuthController
from app.api.v1.billing import BillingController
from app.api.v1.config import ConfigController
from app.api.v1.events import EventsController
from app.api.v1.health import HealthController
from app.api.v1.invoices import InvoiceController
from app.api.v1.payments import PaymentController
from app.api.v1.services import ServiceController
from app.api.v1.spool import SpoolController
from app.api.v1.tariffs import TariffController
from app.api.v1.webhooks import WebhookController


def create_v1_router() -> Router:
    """
    Создать роутер API v1 со всеми контроллерами.

    Returns:
        Router: Корневой роутер API v1
    """
    return Router(
        path="/api/v1",
        route_handlers=[
            AbonentController,
            AuthController,
            BillingController,
            ConfigController,
            EventsController,
            HealthController,
            InvoiceController,
            PaymentController,
            ServiceController,
            SpoolController,
            TariffController,
            WebhookController,
        ],
        tags=["API v1"],
    )
