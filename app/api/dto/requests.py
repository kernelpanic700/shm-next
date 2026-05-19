# =============================================================================
# shm-next — Request DTOs
# =============================================================================
"""
Pydantic-схемы для входящих запросов.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, constr

# === Auth ===

class LoginRequest(BaseModel):
    """Запрос на вход."""
    phone: constr(min_length=10, max_length=20)
    password: constr(min_length=6, max_length=128)


class RegisterRequest(BaseModel):
    """Запрос на регистрацию."""
    full_name: constr(min_length=2, max_length=255)
    phone: constr(min_length=10, max_length=20)
    email: EmailStr | None = None
    password: constr(min_length=6, max_length=128)
    account_number: constr(max_length=20) | None = None


class RefreshTokenRequest(BaseModel):
    """Запрос на обновление токена."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Запрос на смену пароля."""
    old_password: constr(min_length=6, max_length=128)
    new_password: constr(min_length=6, max_length=128)


# === Abonents ===

class AbonentCreateRequest(BaseModel):
    """Запрос на создание абонента."""
    full_name: constr(min_length=2, max_length=255)
    phone: constr(min_length=10, max_length=20)
    account_number: constr(min_length=1, max_length=20)
    balance: float = 0
    currency: str = "RUB"
    allow_negative: bool = False
    tariff_id: UUID | None = None
    metadata: dict | None = None


# Balance top-up request DTO
class BalanceTopUpRequest(BaseModel):
    """Запрос на пополнение баланса абонента."""
    amount: Decimal = Field(..., gt=0, description="Сумма для пополнения баланса")
    payment_method: str = Field(
        default="manual",
        description="Способ оплаты: cash, card, online, terminal, manual",
    )


AbonentCreate = AbonentCreateRequest


class AbonentUpdateRequest(BaseModel):
    """Запрос на обновление абонента."""
    full_name: constr(min_length=2, max_length=255) | None = None
    phone: constr(min_length=10, max_length=20) | None = None
    status: str | None = None
    tariff_id: UUID | None = None
    allow_negative: bool | None = None
    metadata: dict | None = None


AbonentUpdate = AbonentUpdateRequest


class AbonentFilter(BaseModel):
    """Фильтр абонентов."""
    status: str | None = None
    tariff_id: UUID | None = None
    min_balance: float | None = None
    max_balance: float | None = None


# === Payments ===

class PaymentCreate(BaseModel):
    """Запрос на создание платежа."""
    abonent_id: UUID
    amount: float = Field(gt=0, description="Сумма платежа")
    currency: str = "RUB"
    payment_method: str = Field(
        default="cash",
        description="Способ оплаты: cash, card, online, terminal",
    )
    external_id: str | None = Field(
        None, description="Внешний ID платёжной системы"
    )


class PaymentFilter(BaseModel):
    """Фильтр платежей."""
    from_date: datetime | None = None
    to_date: datetime | None = None
    status: str | None = None
    payment_method: str | None = None


# === Services ===

class ServiceCreateRequest(BaseModel):
    """Запрос на подключение услуги."""
    abonent_id: UUID
    service_type: str = Field(..., description="Тип услуги: internet, tv, phone, etc.")
    tariff_service_id: UUID | None = None
    metadata: dict | None = None


class ServiceUpdateRequest(BaseModel):
    """Запрос на обновление услуги."""
    status: str | None = None
    metadata: dict | None = None


# === Tariffs ===

class TariffCreateRequest(BaseModel):
    """Запрос на создание тарифа."""
    name: constr(min_length=1, max_length=255)
    description: str | None = None
    services: list[dict] = []
    is_active: bool = True
    price: float = 0
    currency: str = "RUB"
    billing_period: str = "monthly"


class TariffUpdateRequest(BaseModel):
    """Запрос на обновление тарифа."""
    name: str | None = None
    description: str | None = None
    services: list[dict] | None = None
    is_active: bool | None = None
    price: float | None = None


# === Invoices ===

class InvoiceFilter(BaseModel):
    """Фильтр счетов."""
    status: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None


# === Spool ===

class SpoolTaskCreate(BaseModel):
    """Запрос на создание задачи."""
    action_type: str = Field(..., description="Тип действия")
    payload: dict = Field(default_factory=dict, description="Параметры действия")
    priority: int = Field(default=50, ge=1, le=100, description="Приоритет (1-100)")
    max_retries: int = Field(default=3, ge=0, le=10, description="Макс. попыток")
    execute_after: datetime | None = Field(
        None, description="Выполнить после (ISO 8601)"
    )


# === Webhooks ===

class WebhookCreate(BaseModel):
    """Запрос на создание webhook."""
    url: str = Field(..., description="URL для отправки уведомлений")
    events: list[str] = Field(..., description="Список событий для подписки")
    is_active: bool = True
    secret: str | None = Field(None, description="Секрет для подписи")


# === Billing ===

class WithdrawCreate(BaseModel):
    """Запрос на списание."""
    abonent_id: UUID
    service_id: UUID
    amount: float = Field(gt=0)
    currency: str = "RUB"


# === Notifications ===

class NotificationSendRequest(BaseModel):
    """Запрос на отправку уведомления."""
    abonent_id: UUID
    channel: str = Field(..., description="Канал: email, sms, push")
    subject: str | None = None
    body: str
    template: str | None = None
    template_context: dict | None = None


# === Events ===

class EventFilter(BaseModel):
    """Фильтр событий."""
    action: str | None = None
    resource_type: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=100)
