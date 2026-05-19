# =============================================================================
# shm-next — Billing Events
# =============================================================================
"""Биллинговые события: списания, платежи, циклы, изменения баланса."""

from __future__ import annotations

from app.core.domain.events.event import DomainEvent, EventMetadata
from app.core.domain.value_objects.event_type import EventType


class BillingCycleStartedEvent(DomainEvent):
    """Биллинговый цикл начат."""

    def __init__(
        self,
        cycle_id: str,
        abonent_ids: list[str],
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.BILLING_CYCLE_STARTED, metadata)
        self.cycle_id = cycle_id
        self.abonent_ids = abonent_ids


class BillingCycleCompletedEvent(DomainEvent):
    """Биллинговый цикл завершён."""

    def __init__(
        self,
        cycle_id: str,
        success_count: int,
        fail_count: int,
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.BILLING_CYCLE_COMPLETED, metadata)
        self.cycle_id = cycle_id
        self.success_count = success_count
        self.fail_count = fail_count


class WithdrawCreatedEvent(DomainEvent):
    """Списание создано."""

    def __init__(
        self,
        abonent_id: str,
        withdraw_id: str,
        amount: float,
        currency: str = "RUB",
        service_type: str = "",
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.BILLING_WITHDRAW_CREATED, metadata)
        self.abonent_id = abonent_id
        self.withdraw_id = withdraw_id
        self.amount = amount
        self.currency = currency
        self.service_type = service_type


class WithdrawCompletedEvent(DomainEvent):
    """Списание завершено успешно."""

    def __init__(
        self,
        abonent_id: str,
        withdraw_id: str,
        amount: float,
        currency: str = "RUB",
        service_type: str = "",
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.BILLING_WITHDRAW_COMPLETED, metadata)
        self.abonent_id = abonent_id
        self.withdraw_id = withdraw_id
        self.amount = amount
        self.currency = currency
        self.service_type = service_type


class WithdrawFailedEvent(DomainEvent):
    """Списание не удалось."""

    def __init__(
        self,
        abonent_id: str,
        withdraw_id: str,
        error: str,
        amount: float,
        currency: str = "RUB",
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.BILLING_WITHDRAW_FAILED, metadata)
        self.abonent_id = abonent_id
        self.withdraw_id = withdraw_id
        self.error = error
        self.amount = amount
        self.currency = currency


class BalanceChangedEvent(DomainEvent):
    """Баланс абонента изменён."""

    def __init__(
        self,
        abonent_id: str,
        old_balance: float,
        new_balance: float,
        currency: str = "RUB",
        reason: str = "",
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.BILLING_WITHDRAW_COMPLETED, metadata)
        self.abonent_id = abonent_id
        self.old_balance = old_balance
        self.new_balance = new_balance
        self.currency = currency
        self.reason = reason


class PaymentCompletedEvent(DomainEvent):
    """Платёж завершён успешно."""

    def __init__(
        self,
        abonent_id: str,
        payment_id: str,
        amount: float,
        currency: str = "RUB",
        payment_method: str = "cash",
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.PAYMENT_COMPLETED, metadata)
        self.abonent_id = abonent_id
        self.payment_id = payment_id
        self.amount = amount
        self.currency = currency
        self.payment_method = payment_method


class PaymentFailedEvent(DomainEvent):
    """Платёж не удался."""

    def __init__(
        self,
        abonent_id: str,
        payment_id: str,
        error: str,
        amount: float,
        currency: str = "RUB",
        metadata: EventMetadata | None = None,
    ) -> None:
        super().__init__(EventType.PAYMENT_FAILED, metadata)
        self.abonent_id = abonent_id
        self.payment_id = payment_id
        self.error = error
        self.amount = amount
        self.currency = currency
