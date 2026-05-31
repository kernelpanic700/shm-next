# =============================================================================
# shm-next — Event Types
# =============================================================================
from __future__ import annotations

from enum import Enum


class EventCategory(Enum):
    """Категории событий."""
    BILLING = "billing"
    PAYMENT = "payment"
    ACCOUNT = "account"
    SYSTEM = "system"
    SECURITY = "security"
    INTEGRATION = "integration"
    SPOOL = "spool"


class EventType(Enum):
    """Типы доменных событий."""

    # === Абоненты ===
    ABONENT_CREATED = ("abonent.created", EventCategory.ACCOUNT, False)
    ABONENT_UPDATED = ("abonent.updated", EventCategory.ACCOUNT, False)
    ABONENT_DELETED = ("abonent.deleted", EventCategory.ACCOUNT, True)
    ABONENT_BLOCKED = ("abonent.blocked", EventCategory.ACCOUNT, True)
    ABONENT_ACTIVATED = ("abonent.activated", EventCategory.ACCOUNT, False)
    ABONENT_DEACTIVATED = ("abonent.deactivated", EventCategory.ACCOUNT, False)

    # === Биллинг ===
    BILLING_WITHDRAW_CREATED = ("billing.withdraw_created", EventCategory.BILLING, False)
    BILLING_WITHDRAW_COMPLETED = ("billing.withdraw_completed", EventCategory.BILLING, False)
    BILLING_WITHDRAW_FAILED = ("billing.withdraw_failed", EventCategory.BILLING, True)
    BILLING_CYCLE_STARTED = ("billing.cycle_started", EventCategory.BILLING, False)
    BILLING_CYCLE_COMPLETED = ("billing.cycle_completed", EventCategory.BILLING, False)

    # === Платежи ===
    PAYMENT_CREATED = ("payment.created", EventCategory.PAYMENT, False)
    PAYMENT_COMPLETED = ("payment.completed", EventCategory.PAYMENT, False)
    PAYMENT_FAILED = ("payment.failed", EventCategory.PAYMENT, True)
    PAYMENT_REFUNDED = ("payment.refunded", EventCategory.PAYMENT, False)

    # === Сервисы ===
    SERVICE_ACTIVATED = ("service.activated", EventCategory.INTEGRATION, False)
    SERVICE_DEACTIVATED = ("service.deactivated", EventCategory.INTEGRATION, False)
    SERVICE_RENEWED = ("service.renewed", EventCategory.INTEGRATION, False)
    SERVICE_ERROR = ("service.error", EventCategory.INTEGRATION, True)

    # === Spool ===
    SPOOL_TASK_CREATED = ("spool.task_created", EventCategory.SPOOL, False)
    SPOOL_TASK_STARTED = ("spool.task_started", EventCategory.SPOOL, False)
    SPOOL_TASK_COMPLETED = ("spool.task_completed", EventCategory.SPOOL, False)
    SPOOL_TASK_FAILED = ("spool.task_failed", EventCategory.SPOOL, True)
    SPOOL_TASK_DLQ = ("spool.task_dlq", EventCategory.SPOOL, True)

    # === Система ===
    SYSTEM_STARTUP = ("system.startup", EventCategory.SYSTEM, False)
    SYSTEM_SHUTDOWN = ("system.shutdown", EventCategory.SYSTEM, False)
    SYSTEM_HEALTH_CHECK = ("system.health_check", EventCategory.SYSTEM, False)

    def __init__(self, value: str, category: EventCategory, critical: bool):
        self._value_ = value
        self._category = category
        self._critical = critical

    def category(self) -> EventCategory:
        return self._category

    def is_critical(self) -> bool:
        return self._critical
