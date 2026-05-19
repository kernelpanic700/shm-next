# =============================================================================
# shm-next — Status Enums
# =============================================================================
"""
Перечисления статусов для доменных сущностей.

Используются как type-safe альтернативы строковым/числовым статусам
из оригинальной Perl-системы.
"""

from __future__ import annotations

from enum import StrEnum


class ServiceStatus(StrEnum):
    """Статус услуги абонента."""
    INIT = "INIT"           # Инициализация
    PROGRESS = "PROGRESS"   # В процессе активации
    ACTIVE = "ACTIVE"       # Активна
    BLOCKED = "BLOCKED"     # Заблокирована
    WAIT_FOR_PAY = "WAIT_FOR_PAY"  # Ожидание оплаты
    REMOVED = "REMOVED"     # Удалена
    DELETED = "DELETED"     # Полностью удалена

    def is_active(self) -> bool:
        return self in (ServiceStatus.ACTIVE, ServiceStatus.PROGRESS)

    def is_terminal(self) -> bool:
        return self in (ServiceStatus.REMOVED, ServiceStatus.DELETED)


class AbonentStatus(StrEnum):
    """Статус абонента."""
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    DELETED = "DELETED"
    INACTIVE = "INACTIVE"


class PaymentStatus(StrEnum):
    """Статус платежа."""
    NEW = "NEW"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class WithdrawStatus(StrEnum):
    """Статус списания."""
    NEW = "NEW"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SpoolStatus(StrEnum):
    """Статус задачи во внешнем Action Engine."""
    NEW = "NEW"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    STUCK = "STUCK"          # Исчерпаны ретраи, в DLQ
    DELAYED = "DELAYED"      # Отложена (circuit breaker)
    CANCELLED = "CANCELLED"


class InvoiceStatus(StrEnum):
    """Статус счёта."""
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class SessionStatus(StrEnum):
    """Статус сессии."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
