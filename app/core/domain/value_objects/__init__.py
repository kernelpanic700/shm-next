"""Value Objects — неизменяемые типы данных доменного слоя."""

from app.core.domain.value_objects.abonent import AbonentStatus
from app.core.domain.value_objects.account_number import AccountNumber
from app.core.domain.value_objects.base import ValueObject
from app.core.domain.value_objects.currency import Currency
from app.core.domain.value_objects.email import Email
from app.core.domain.value_objects.event_type import EventCategory, EventType
from app.core.domain.value_objects.money import CurrencyMismatchError, Money
from app.core.domain.value_objects.payment import PaymentStatus
from app.core.domain.value_objects.period import Period
from app.core.domain.value_objects.phone_number import PhoneNumber
from app.core.domain.value_objects.service import ServiceStatus
from app.core.domain.value_objects.spool import SpoolStatus
from app.core.domain.value_objects.uuid_value import UUIDValue
from app.core.domain.value_objects.withdraw import WithdrawStatus

__all__ = [
    "AbonentStatus",
    "AccountNumber",
    "Currency",
    "CurrencyMismatchError",
    "Email",
    "EventCategory",
    "EventType",
    "Money",
    "PaymentStatus",
    "Period",
    "PhoneNumber",
    "ServiceStatus",
    "SpoolStatus",
    "UUIDValue",
    "ValueObject",
    "WithdrawStatus",
]
