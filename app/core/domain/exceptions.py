# =============================================================================
# shm-next — Domain Exceptions
# =============================================================================
"""
Доменные исключения для бизнес-логики.
"""

from __future__ import annotations


class DomainError(Exception):
    """Базовое доменное исключение."""

    def __init__(self, message: str = "Domain error occurred"):
        self.message = message
        super().__init__(self.message)


class InsufficientBalanceError(DomainError):
    """Недостаточно средств на балансе."""

    def __init__(self, required: float, available: float, currency: str = "RUB"):
        self.required = required
        self.available = available
        self.currency = currency
        super().__init__(
            f"Insufficient balance: required {required} {currency}, available {available} {currency}"
        )


class ServiceNotActiveError(DomainError):
    """Услуга не активна."""

    def __init__(self, service_id: str):
        self.service_id = service_id
        super().__init__(f"Service {service_id} is not active")


class ObjectNotFoundError(DomainError):
    """Объект не найден."""

    def __init__(self, object_type: str, object_id: str):
        self.object_type = object_type
        self.object_id = object_id
        super().__init__(f"{object_type} with id {object_id} not found")


class ValidationError(DomainError):
    """Ошибка валидации."""

    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"Validation error for field '{field}': {value}")


class BusinessRuleViolationError(DomainError):
    """Нарушение бизнес-правила."""

    def __init__(self, rule: str, details: str = ""):
        self.rule = rule
        super().__init__(f"Business rule violation: {rule}. {details}" if details else f"Business rule violation: {rule}")
