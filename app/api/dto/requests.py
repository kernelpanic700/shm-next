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
    login: str | None = Field(default=None, min_length=1, max_length=128)
    login2: str | None = Field(default=None, min_length=1, max_length=128)
    email: EmailStr | None = None
    balance: float = 0
    currency: str = "RUB"
    allow_negative: bool = False
    tariff_id: UUID | None = None
    partner_id: UUID | None = None
    discount: float = Field(default=0, ge=0, le=100)
    credit: float = Field(default=0, ge=0)
    bonus: float = Field(default=0, ge=0)
    comment: str | None = Field(default=None, max_length=2000)
    contract: str | None = Field(default=None, max_length=32)
    can_overdraft: bool = False
    verified: bool = False
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
    login: str | None = Field(default=None, min_length=1, max_length=128)
    login2: str | None = Field(default=None, min_length=1, max_length=128)
    email: EmailStr | None = None
    status: str | None = None
    tariff_id: UUID | None = None
    allow_negative: bool | None = None
    partner_id: UUID | None = None
    discount: float | None = Field(default=None, ge=0, le=100)
    credit: float | None = Field(default=None, ge=0)
    bonus: float | None = Field(default=None, ge=0)
    comment: str | None = Field(default=None, max_length=2000)
    contract: str | None = Field(default=None, max_length=32)
    can_overdraft: bool | None = None
    verified: bool | None = None
    metadata: dict | None = None


AbonentUpdate = AbonentUpdateRequest


class AbonentFilter(BaseModel):
    """Фильтр абонентов."""
    status: str | None = None
    tariff_id: UUID | None = None
    min_balance: float | None = None
    max_balance: float | None = None


class AbonentProfileUpsertRequest(BaseModel):
    """SHM-style arbitrary JSON profile."""
    data: dict = Field(default_factory=dict)


class AbonentStorageUpsertRequest(BaseModel):
    """SHM-style per-abonent named storage item."""
    data: dict | str
    content_type: str = Field(default="application/json", max_length=128)
    user_service_id: UUID | None = None
    settings: dict | None = None


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


class ServiceRenewRequest(BaseModel):
    """Запрос на продление SHM-услуги."""
    abonent_discount_percent: int = Field(default=0, ge=0, le=100)
    bonus_balance: Decimal | None = Field(default=None, ge=0)


class ServiceStopRequest(BaseModel):
    """Запрос на остановку SHM-услуги."""
    reason: str = Field(default="user_request", min_length=1, max_length=128)


class CatalogServiceCreateRequest(BaseModel):
    """Запрос на создание каталожной SHM-услуги."""
    name: constr(min_length=1, max_length=64)
    cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    period_cost: Decimal = Field(default=Decimal("1.0000"), ge=0)
    category: str | None = Field(default=None, max_length=16)
    children: list[UUID] = Field(default_factory=list)
    next_service_id: UUID | None = None
    legacy_service_id: int | None = None
    allow_to_order: bool = True
    max_count: int | None = Field(default=None, ge=1)
    question: bool = False
    pay_always: bool = False
    no_discount: bool = False
    description: str | None = Field(default=None, max_length=255)
    pay_in_credit: bool = False
    config: dict | None = None
    is_composite: bool = False


class CatalogServiceUpdateRequest(BaseModel):
    """Запрос на обновление каталожной SHM-услуги."""
    name: str | None = Field(default=None, min_length=1, max_length=64)
    cost: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    period_cost: Decimal | None = Field(default=None, ge=0)
    category: str | None = Field(default=None, max_length=16)
    children: list[UUID] | None = None
    next_service_id: UUID | None = None
    legacy_service_id: int | None = None
    allow_to_order: bool | None = None
    max_count: int | None = Field(default=None, ge=1)
    question: bool | None = None
    pay_always: bool | None = None
    no_discount: bool | None = None
    description: str | None = Field(default=None, max_length=255)
    pay_in_credit: bool | None = None
    config: dict | None = None
    is_composite: bool | None = None
    is_deleted: bool | None = None


class CatalogServiceOrderRequest(BaseModel):
    """Запрос на заказ SHM-услуги абонентом."""
    abonent_id: UUID
    quantity: int = Field(default=1, ge=1)
    abonent_discount_percent: int = Field(default=0, ge=0, le=100)
    bonus_balance: Decimal | None = Field(default=None, ge=0)
    metadata: dict | None = None


class EventActionRuleCreateRequest(BaseModel):
    """Запрос на создание правила действия по событию."""
    event_type: str = Field(..., min_length=1, max_length=64)
    action_type: str = Field(..., min_length=1, max_length=100)
    title: str | None = Field(default=None, max_length=128)
    service_type: str | None = Field(default=None, max_length=64)
    catalog_service_id: UUID | None = None
    server_group_id: UUID | None = None
    server_id: UUID | None = None
    template_id: UUID | None = None
    command: str | None = Field(default=None, max_length=8000)
    settings: dict | None = None
    priority: int = Field(default=50, ge=0, le=100)
    max_retries: int = Field(default=3, ge=1, le=10)
    is_enabled: bool = True


class EventActionRuleUpdateRequest(BaseModel):
    """Запрос на обновление правила действия по событию."""
    event_type: str | None = Field(default=None, min_length=1, max_length=64)
    action_type: str | None = Field(default=None, min_length=1, max_length=100)
    title: str | None = Field(default=None, max_length=128)
    service_type: str | None = Field(default=None, max_length=64)
    catalog_service_id: UUID | None = None
    server_group_id: UUID | None = None
    server_id: UUID | None = None
    template_id: UUID | None = None
    command: str | None = Field(default=None, max_length=8000)
    settings: dict | None = None
    priority: int | None = Field(default=None, ge=0, le=100)
    max_retries: int | None = Field(default=None, ge=1, le=10)
    is_enabled: bool | None = None


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
    currency: str | None = None
    billing_period: str | None = None


# === Invoices ===

class InvoiceCreateRequest(BaseModel):
    """Запрос на создание счёта."""
    abonent_id: UUID
    amount: float = Field(gt=0, description="Сумма счёта")
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    period_start: datetime | None = None
    period_end: datetime | None = None
    due_date: datetime | None = None
    description: str | None = Field(default=None, max_length=2000)
    metadata: dict | None = None
    issue_now: bool = True


class InvoiceFilter(BaseModel):
    """Фильтр счетов."""
    status: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None


# === Bonuses and Discounts ===

class BonusEntryCreateRequest(BaseModel):
    """Запрос на начисление бонуса абоненту."""
    abonent_id: UUID
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    reason: str = Field(default="", max_length=500)
    expires_at: datetime | None = None
    source: str = Field(default="manual", min_length=1, max_length=50)


class DiscountCreateRequest(BaseModel):
    """Запрос на создание скидки."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    discount_type: str = Field(default="percent", pattern="^(percent|fixed|relative)$")
    value: Decimal = Field(..., ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    is_active: bool = True
    max_uses: int | None = Field(default=None, ge=1)


class DiscountUpdateRequest(BaseModel):
    """Запрос на обновление скидки."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    discount_type: str | None = Field(default=None, pattern="^(percent|fixed|relative)$")
    value: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    is_active: bool | None = None
    max_uses: int | None = Field(default=None, ge=1)


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


# === Automation ===

class SSHKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    private_key: str = Field(..., min_length=1)
    public_key: str | None = None
    passphrase: str | None = None
    fingerprint: str | None = None
    is_active: bool = True


class SSHKeyUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    private_key: str | None = Field(default=None, min_length=1)
    public_key: str | None = None
    passphrase: str | None = None
    fingerprint: str | None = None
    is_active: bool | None = None


class ServerGroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    transport: str = Field(default="ssh", pattern="^(ssh|http|mail|telegram|local)$")
    strategy: str = Field(default="round_robin", pattern="^(round_robin|first_active)$")
    settings: dict | None = None
    is_active: bool = True


class ServerGroupUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    transport: str | None = Field(default=None, pattern="^(ssh|http|mail|telegram|local)$")
    strategy: str | None = Field(default=None, pattern="^(round_robin|first_active)$")
    settings: dict | None = None
    is_active: bool | None = None


class ServerCreateRequest(BaseModel):
    group_id: UUID
    name: str = Field(..., min_length=1, max_length=128)
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(default=22, ge=1, le=65535)
    key_id: UUID | None = None
    proxy_jump: str | None = Field(default=None, max_length=255)
    default_cmd: str | None = Field(default=None, max_length=8000)
    settings: dict | None = None
    is_active: bool = True


class ServerUpdateRequest(BaseModel):
    group_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=128)
    host: str | None = Field(default=None, min_length=1, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    key_id: UUID | None = None
    proxy_jump: str | None = Field(default=None, max_length=255)
    default_cmd: str | None = Field(default=None, max_length=8000)
    settings: dict | None = None
    is_active: bool | None = None


class CommandTemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    transport: str = Field(default="ssh", pattern="^(ssh|http|mail|telegram|local)$")
    body: str = Field(..., min_length=1)
    description: str | None = None
    is_active: bool = True


class CommandTemplateUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    transport: str | None = Field(default=None, pattern="^(ssh|http|mail|telegram|local)$")
    body: str | None = Field(default=None, min_length=1)
    description: str | None = None
    is_active: bool | None = None


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
