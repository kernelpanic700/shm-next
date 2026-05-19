# =============================================================================
# shm-next — SQLAlchemy Models (compatibility shim)
# =============================================================================
"""
Обратная совместимость: все модели доступны из models.py.
Используйте app.infrastructure.db.models.<name> для новых импортов.
"""

from app.infrastructure.db.models import (
    AbonentModel,
    AuditLogModel,
    Base,
    BonusEntryModel,
    DiscountModel,
    InvoiceModel,
    NotificationModel,
    PaymentModel,
    ServiceModel,
    SessionModel,
    SpoolTaskModel,
    TariffModel,
    TariffServiceModel,
    WebhookModel,
    WithdrawModel,
)

__all__ = [
    "AbonentModel",
    "AuditLogModel",
    "Base",
    "BonusEntryModel",
    "DiscountModel",
    "InvoiceModel",
    "NotificationModel",
    "PaymentModel",
    "ServiceModel",
    "SessionModel",
    "SpoolTaskModel",
    "TariffModel",
    "TariffServiceModel",
    "WebhookModel",
    "WithdrawModel",
]
