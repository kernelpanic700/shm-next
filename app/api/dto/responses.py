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

from pydantic import BaseModel, Field, model_validator


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

    @model_validator(mode='before')
    @classmethod
    def validate_abonent(cls, data):
        """Custom validation to handle domain entity Abonent and SQLAlchemy models."""
        from app.core.domain.entities.abonent import Abonent
        from app.core.domain.value_objects import AbonentStatus, Money

        # If data is already a dict, just pass it through
        if isinstance(data, dict):
            return data

        # If data is the domain entity Abonent, extract fields properly
        if isinstance(data, Abonent):
            status_val = data.status.value if isinstance(data.status, AbonentStatus) else data.status

            if isinstance(data.balance, Money):
                balance_val = float(data.balance.amount)
                currency_val = data.balance.currency.value
            else:
                balance_val = float(data.balance)
                currency_val = 'RUB'

            return {
                'id': data.id,
                'full_name': data.full_name,
                'phone': data.phone,
                'account_number': data.account_number,
                'balance': balance_val,
                'currency': currency_val,
                'status': status_val,
                'tariff_id': data.tariff_id,
                'allow_negative': data.allow_negative,
                'created_at': data.created_at,
                'updated_at': data.updated_at,
            }

        # If data is a SQLAlchemy model, extract values from attributes
        if hasattr(data, '__dict__'):
            balance_attr = getattr(data, 'balance', None)
            currency_attr = getattr(data, 'currency', None)
            status_attr = getattr(data, 'status', None)

            if hasattr(balance_attr, 'amount'):
                balance_val = float(balance_attr.amount)
                currency_val = balance_attr.currency.value if hasattr(balance_attr, 'currency') else (currency_attr or 'RUB')
            else:
                balance_val = float(balance_attr) if balance_attr is not None else 0.0
                currency_val = currency_attr or 'RUB'

            if hasattr(status_attr, 'value'):
                status_val = status_attr.value
            else:
                status_val = str(status_attr) if status_attr else 'ACTIVE'

            return {
                'id': getattr(data, 'id', None),
                'full_name': getattr(data, 'full_name', ''),
                'phone': getattr(data, 'phone', ''),
                'account_number': getattr(data, 'account_number', ''),
                'balance': balance_val,
                'currency': currency_val,
                'status': status_val,
                'tariff_id': getattr(data, 'tariff_id', None),
                'allow_negative': getattr(data, 'allow_negative', False),
                'created_at': getattr(data, 'created_at', None),
                'updated_at': getattr(data, 'updated_at', None),
            }

        return data


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

    @model_validator(mode="before")
    @classmethod
    def validate_tariff(cls, data):
        from app.core.domain.entities.tariff import Tariff

        if isinstance(data, dict):
            return data
        if isinstance(data, Tariff):
            return {
                "id": data.id,
                "name": data.name,
                "description": data.description,
                "services": data.services,
                "is_active": data.is_active,
                "price": data.price,
                "currency": data.currency,
                "billing_period": data.billing_period,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


class TariffListResponse(BaseModel):
    """Список тарифов."""
    items: list[TariffResponse]
    total: int


class ServiceResponse(BaseModel):
    """Ответ с данными услуги."""
    id: UUID
    abonent_id: UUID
    service_type: str
    tariff_service_id: UUID | None = None
    catalog_service_id: UUID | None = None
    status: str
    activated_at: datetime | None = None
    deactivated_at: datetime | None = None
    expire_at: datetime | None = None
    cost: float
    currency: str
    period_cost: str | None = None
    next_service_id: UUID | None = None
    parent_id: UUID | None = None
    quantity: int = 1
    auto_bill: bool = True
    pay_always: bool = False
    pay_in_credit: bool = False
    no_discount: bool = False
    metadata: dict = {}


class ServiceListResponse(BaseModel):
    """Список услуг с пагинацией."""
    items: list[ServiceResponse]
    total: int
    page: int
    per_page: int


class CatalogServiceResponse(BaseModel):
    """Ответ с данными каталожной SHM-услуги."""
    id: UUID
    name: str
    cost: float
    currency: str
    period_cost: str
    category: str | None = None
    children: list[UUID]
    next_service_id: UUID | None = None
    legacy_service_id: int | None = None
    allow_to_order: bool
    max_count: int | None = None
    question: bool
    pay_always: bool
    no_discount: bool
    description: str | None = None
    pay_in_credit: bool
    config: dict
    is_composite: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def validate_catalog_service(cls, data):
        from app.core.domain.entities.catalog_service import CatalogService

        if isinstance(data, dict):
            return data
        if isinstance(data, CatalogService):
            return {
                "id": data.id,
                "name": data.name,
                "cost": float(data.cost.amount),
                "currency": data.cost.currency.value,
                "period_cost": str(data.period_cost),
                "category": data.category,
                "children": data.children,
                "next_service_id": data.next_service_id,
                "legacy_service_id": data.legacy_service_id,
                "allow_to_order": data.allow_to_order,
                "max_count": data.max_count,
                "question": data.question,
                "pay_always": data.pay_always,
                "no_discount": data.no_discount,
                "description": data.description,
                "pay_in_credit": data.pay_in_credit,
                "config": data.config,
                "is_composite": data.is_composite,
                "is_deleted": data.is_deleted,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


class CatalogServiceListResponse(BaseModel):
    """Список каталожных SHM-услуг."""
    items: list[CatalogServiceResponse]
    total: int


class EventActionRuleResponse(BaseModel):
    """Ответ с данными правила действия по событию."""
    id: UUID
    event_type: str
    action_type: str
    title: str
    service_type: str | None = None
    catalog_service_id: UUID | None = None
    settings: dict
    priority: int
    max_retries: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def validate_event_action_rule(cls, data):
        from app.core.domain.entities.event_action_rule import EventActionRule

        if isinstance(data, dict):
            return data
        if isinstance(data, EventActionRule):
            return {
                "id": data.id,
                "event_type": data.event_type,
                "action_type": data.action_type,
                "title": data.title,
                "service_type": data.service_type,
                "catalog_service_id": data.catalog_service_id,
                "settings": data.settings,
                "priority": data.priority,
                "max_retries": data.max_retries,
                "is_enabled": data.is_enabled,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


class EventActionRuleListResponse(BaseModel):
    """Список правил действий по событиям."""
    items: list[EventActionRuleResponse]
    total: int


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
    description: str | None = None
    metadata: dict = {}
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def validate_invoice(cls, data):
        from app.core.domain.entities.invoice import Invoice

        if isinstance(data, dict):
            return data
        if isinstance(data, Invoice):
            return {
                "id": data.id,
                "abonent_id": data.abonent_id,
                "amount": data.amount,
                "currency": data.currency,
                "status": data.status,
                "period_start": data.period_start,
                "period_end": data.period_end,
                "due_date": data.due_date,
                "description": data.description,
                "metadata": data.meta,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


class BonusEntryResponse(BaseModel):
    """Ответ с данными бонусной записи."""
    id: UUID
    abonent_id: UUID
    amount: float
    currency: str
    reason: str
    expires_at: datetime | None = None
    is_active: bool
    source: str
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def validate_bonus_entry(cls, data):
        from app.core.domain.entities.bonus_entry import BonusEntry
        from app.core.domain.value_objects import Money

        if isinstance(data, dict):
            return data
        if isinstance(data, BonusEntry):
            amount = data.amount or Money.zero("RUB")
            return {
                "id": data.id,
                "abonent_id": data.abonent_id,
                "amount": float(amount.amount),
                "currency": amount.currency.value,
                "reason": data.reason,
                "expires_at": data.expires_at,
                "is_active": data.is_active,
                "source": data.source,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


class BonusEntryListResponse(BaseModel):
    """Список бонусных записей."""
    items: list[BonusEntryResponse]
    total: int


class DiscountResponse(BaseModel):
    """Ответ с данными скидки."""
    id: UUID
    name: str
    description: str
    discount_type: str
    value: float
    currency: str
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    is_active: bool
    max_uses: int | None = None
    used_count: int
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def validate_discount(cls, data):
        from app.core.domain.entities.discount import Discount

        if isinstance(data, dict):
            return data
        if isinstance(data, Discount):
            return {
                "id": data.id,
                "name": data.name,
                "description": data.description,
                "discount_type": data.discount_type,
                "value": float(data.value),
                "currency": data.currency,
                "valid_from": data.valid_from,
                "valid_to": data.valid_to,
                "is_active": data.is_active,
                "max_uses": data.max_uses,
                "used_count": data.used_count,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


class DiscountListResponse(BaseModel):
    """Список скидок."""
    items: list[DiscountResponse]
    total: int


class TokenResponse(BaseModel):
    """Ответ с токенами авторизации."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AbonentListResponse(BaseModel):
    """Список абонентов с пагинацией."""
    items: list[AbonentResponse]
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
