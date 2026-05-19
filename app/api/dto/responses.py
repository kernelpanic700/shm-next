# =============================================================================
# shm-next — Response DTOs
# =============================================================================
"""
Pydantic-схемы для исходящих ответов.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """Стандартный ответ API."""
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class WithdrawResponse(BaseModel):
    """Ответ на запрос списания."""
    withdraw_id: UUID
    amount: float
    currency: str
    status: str
    created_at: datetime


class PaymentResponse(BaseModel):
    """Ответ с данными платежа."""
    id: UUID
    abonent_id: UUID
    amount: float
    currency: str
    payment_method: str
    status: str
    external_id: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class PaymentListResponse(BaseModel):
    """Список платежей с пагинацией."""
    items: list[dict]
    total: int
    page: int
    per_page: int


class SpoolTaskResponse(BaseModel):
    """Ответ с данными задачи."""
    id: int
    action_type: str
    status: str
    priority: int
    retry_count: int
    max_retries: int
    created_at: datetime
    execute_after: datetime | None = None


class AuditLogResponse(BaseModel):
    """Ответ с данными аудиторской записи."""
    id: int
    actor_id: UUID | None = None
    action: str
    resource_type: str
    resource_id: str
    old_values: dict | None = None
    new_values: dict | None = None
    created_at: datetime


class WebhookResponse(BaseModel):
    """Ответ с данными webhook."""
    id: UUID
    url: str
    events: list[str]
    is_active: bool
    created_at: datetime


class AbonentResponse(BaseModel):
    """Ответ с данными абонента."""
    id: UUID
    full_name: str
    phone: str
    account_number: str
    balance: float
    currency: str
    status: str
    tariff_id: UUID | None = None
    allow_negative: bool
    created_at: datetime
    updated_at: datetime


class TariffResponse(BaseModel):
    """Ответ с данными тарифа."""
    id: UUID
    name: str
    description: str | None = None
    services: list[dict]
    is_active: bool
    price: float
    currency: str
    billing_period: str
    created_at: datetime
    updated_at: datetime


class TariffListResponse(BaseModel):
    """Список тарифов."""
    items: list[TariffResponse]
    total: int


class ServiceResponse(BaseModel):
    """Ответ с данными услуги."""
    id: UUID
    abonent_id: UUID
    service_type: str
    status: str
    activated_at: datetime | None = None
    deactivated_at: datetime | None = None
    cost: float
    currency: str


class ServiceListResponse(BaseModel):
    """Список услуг с пагинацией."""
    items: list[dict]
    total: int
    page: int
    per_page: int


class NotificationResponse(BaseModel):
    """Ответ с данными уведомления."""
    id: UUID
    abonent_id: UUID
    channel: str
    subject: str | None = None
    body: str
    status: str
    sent_at: datetime | None = None
    created_at: datetime


class InvoiceResponse(BaseModel):
    """Ответ с данными счёта."""
    id: UUID
    abonent_id: UUID
    amount: float
    currency: str
    status: str
    period_start: datetime | None = None
    period_end: datetime | None = None
    due_date: datetime | None = None
    created_at: datetime


class TokenResponse(BaseModel):
    """Ответ с токенами авторизации."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AbonentListResponse(BaseModel):
    """Список абонентов с пагинацией."""
    items: list[dict]
    total: int
    page: int
    per_page: int
    pages: int


class BalanceResponse(BaseModel):
    """Ответ с балансом абонента."""
    balance: float
    currency: str
    available: bool
    allow_negative: bool


class TariffInfoResponse(BaseModel):
    """Ответ с информацией о тарифе."""
    tariff_id: UUID | None = None
    name: str | None = None
    price: float | None = None
    currency: str | None = None


class PaginatedResponse(BaseModel):
    """Базовый ответ с пагинацией."""
    items: list[dict]
    total: int
    page: int
    per_page: int
    pages: int
