# =============================================================================
# shm-next — SQLAlchemy Models
# =============================================================================
"""
Модели базы данных SQLAlchemy 2.0.

Все модели наследуются от Base и используют asyncpg как драйвер.
"""

from app.infrastructure.db.models.abonent import AbonentModel, AbonentProfileModel, AbonentStorageModel
from app.infrastructure.db.models.audit_log import AuditLogModel
from app.infrastructure.db.models.base import Base
from app.infrastructure.db.models.bonus_entry import BonusEntryModel
from app.infrastructure.db.models.catalog_service import CatalogServiceModel
from app.infrastructure.db.models.automation import CommandTemplateModel, ServerGroupModel, ServerModel, SSHKeyModel
from app.infrastructure.db.models.discount import DiscountModel
from app.infrastructure.db.models.event_action_rule import EventActionRuleModel
from app.infrastructure.db.models.invoice import InvoiceModel
from app.infrastructure.db.models.notification import NotificationModel
from app.infrastructure.db.models.payment import PaymentModel
from app.infrastructure.db.models.service import ServiceModel
from app.infrastructure.db.models.session import SessionModel
from app.infrastructure.db.models.spool_task import SpoolTaskModel
from app.infrastructure.db.models.tariff import TariffModel, TariffServiceModel
from app.infrastructure.db.models.webhook import WebhookModel
from app.infrastructure.db.models.withdraw import WithdrawModel

__all__ = [
    "AbonentModel",
    "AbonentProfileModel",
    "AbonentStorageModel",
    "AuditLogModel",
    "Base",
    "BonusEntryModel",
    "CatalogServiceModel",
    "CommandTemplateModel",
    "DiscountModel",
    "EventActionRuleModel",
    "InvoiceModel",
    "NotificationModel",
    "PaymentModel",
    "ServiceModel",
    "ServerGroupModel",
    "ServerModel",
    "SessionModel",
    "SSHKeyModel",
    "SpoolTaskModel",
    "TariffModel",
    "TariffServiceModel",
    "WebhookModel",
    "WithdrawModel",
]
