# =============================================================================
# shm-next — Repository Protocols
# =============================================================================
from app.core.domain.repositories.abonent import AbonentRepositoryProtocol
from app.core.domain.repositories.base import BaseRepository
from app.core.domain.repositories.billing import BillingRepositoryProtocol
from app.core.domain.repositories.bonus_entry import BonusEntryRepositoryProtocol
from app.core.domain.repositories.catalog_service import CatalogServiceRepositoryProtocol
from app.core.domain.repositories.discount import DiscountRepositoryProtocol
from app.core.domain.repositories.event_action_rule import EventActionRuleRepositoryProtocol
from app.core.domain.repositories.invoice import InvoiceRepositoryProtocol
from app.core.domain.repositories.payment import PaymentRepositoryProtocol
from app.core.domain.repositories.service import ServiceRepositoryProtocol
from app.core.domain.repositories.session import SessionRepositoryProtocol
from app.core.domain.repositories.spool import SpoolRepositoryProtocol
from app.core.domain.repositories.tariff import TariffRepositoryProtocol
from app.core.domain.repositories.tariff_service import TariffServiceRepositoryProtocol
from app.core.domain.repositories.withdraw import WithdrawRepositoryProtocol

__all__ = [
    "AbonentRepositoryProtocol",
    "BaseRepository",
    "BillingRepositoryProtocol",
    "BonusEntryRepositoryProtocol",
    "CatalogServiceRepositoryProtocol",
    "DiscountRepositoryProtocol",
    "EventActionRuleRepositoryProtocol",
    "InvoiceRepositoryProtocol",
    "PaymentRepositoryProtocol",
    "ServiceRepositoryProtocol",
    "SessionRepositoryProtocol",
    "SpoolRepositoryProtocol",
    "TariffRepositoryProtocol",
    "TariffServiceRepositoryProtocol",
    "WithdrawRepositoryProtocol",
]
