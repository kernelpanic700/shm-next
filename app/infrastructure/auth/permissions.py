# =============================================================================
# shm-next — Permissions System
# =============================================================================
"""
Система прав доступа (RBAC + ABAC).

Определяет роли и разрешения для различных операций.
"""

from __future__ import annotations

from uuid import UUID


class Role:
    """Роли пользователей."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    ABONENT = "abonent"


class Permission:
    """Разрешения системы."""
    # Собственный кабинет абонента
    SELF_READ = "self:read"
    SELF_WRITE = "self:write"

    # Абоненты
    ABONENTS_READ = "abonents:read"
    ABONENTS_WRITE = "abonents:write"
    ABONENTS_DELETE = "abonents:delete"

    # Тарифы
    TARIFFS_READ = "tariffs:read"
    TARIFFS_WRITE = "tariffs:write"

    # Биллинг
    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"
    BILLING_FORCE = "billing:force"  # Принудительное списание

    # Платежи
    PAYMENTS_READ = "payments:read"
    PAYMENTS_WRITE = "payments:write"
    PAYMENTS_REFUND = "payments:refund"

    # Услуги и каталог
    SERVICES_READ = "services:read"
    SERVICES_WRITE = "services:write"
    CATALOG_READ = "catalog:read"
    CATALOG_WRITE = "catalog:write"

    # Счета, скидки, бонусы, события и интеграции
    INVOICES_READ = "invoices:read"
    INVOICES_WRITE = "invoices:write"
    DISCOUNTS_READ = "discounts:read"
    DISCOUNTS_WRITE = "discounts:write"
    BONUS_READ = "bonus:read"
    BONUS_WRITE = "bonus:write"
    EVENTS_READ = "events:read"
    EVENTS_WRITE = "events:write"
    WEBHOOKS_READ = "webhooks:read"
    WEBHOOKS_WRITE = "webhooks:write"

    # Спул
    SPOOL_READ = "spool:read"
    SPOOL_WRITE = "spool:write"
    SPOOL_RETRY = "spool:retry"

    # Администрирование
    USERS_MANAGE = "users:manage"
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"
    AUDIT_READ = "audit:read"

    # Сессии
    SESSIONS_MANAGE = "sessions:manage"


# Маппинг: роль → набор прав
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    Role.SUPER_ADMIN: frozenset([
        "*",  # Все права
    ]),
    Role.ADMIN: frozenset([
        Permission.ABONENTS_READ,
        Permission.ABONENTS_WRITE,
        Permission.TARIFFS_READ,
        Permission.TARIFFS_WRITE,
        Permission.BILLING_READ,
        Permission.BILLING_WRITE,
        Permission.PAYMENTS_READ,
        Permission.PAYMENTS_WRITE,
        Permission.PAYMENTS_REFUND,
        Permission.SERVICES_READ,
        Permission.SERVICES_WRITE,
        Permission.CATALOG_READ,
        Permission.CATALOG_WRITE,
        Permission.INVOICES_READ,
        Permission.INVOICES_WRITE,
        Permission.DISCOUNTS_READ,
        Permission.DISCOUNTS_WRITE,
        Permission.BONUS_READ,
        Permission.BONUS_WRITE,
        Permission.EVENTS_READ,
        Permission.EVENTS_WRITE,
        Permission.WEBHOOKS_READ,
        Permission.WEBHOOKS_WRITE,
        Permission.SPOOL_READ,
        Permission.SPOOL_WRITE,
        Permission.SPOOL_RETRY,
        Permission.CONFIG_READ,
        Permission.CONFIG_WRITE,
        Permission.AUDIT_READ,
        Permission.SESSIONS_MANAGE,
    ]),
    Role.MANAGER: frozenset([
        Permission.ABONENTS_READ,
        Permission.ABONENTS_WRITE,
        Permission.TARIFFS_READ,
        Permission.BILLING_READ,
        Permission.PAYMENTS_READ,
        Permission.SERVICES_READ,
        Permission.CATALOG_READ,
        Permission.INVOICES_READ,
        Permission.DISCOUNTS_READ,
        Permission.BONUS_READ,
        Permission.SPOOL_READ,
        Permission.CONFIG_READ,
    ]),
    Role.OPERATOR: frozenset([
        Permission.ABONENTS_READ,
        Permission.BILLING_READ,
        Permission.PAYMENTS_READ,
        Permission.SERVICES_READ,
        Permission.CATALOG_READ,
        Permission.SPOOL_READ,
    ]),
    Role.ABONENT: frozenset([
        Permission.SELF_READ,
        Permission.SELF_WRITE,
    ]),
}


READ_METHODS = {"GET", "HEAD", "OPTIONS"}

ADMIN_ROUTE_RULES: tuple[tuple[str, str, str], ...] = (
    ("/api/v1/abonents", Permission.ABONENTS_READ, Permission.ABONENTS_WRITE),
    ("/api/v1/bonus-entries", Permission.BONUS_READ, Permission.BONUS_WRITE),
    ("/api/v1/catalog-services", Permission.CATALOG_READ, Permission.CATALOG_WRITE),
    ("/api/v1/discounts", Permission.DISCOUNTS_READ, Permission.DISCOUNTS_WRITE),
    ("/api/v1/event-action-rules", Permission.EVENTS_READ, Permission.EVENTS_WRITE),
    ("/api/v1/events", Permission.EVENTS_READ, Permission.EVENTS_WRITE),
    ("/api/v1/invoices", Permission.INVOICES_READ, Permission.INVOICES_WRITE),
    ("/api/v1/spool", Permission.SPOOL_READ, Permission.SPOOL_WRITE),
    ("/api/v1/tariffs", Permission.TARIFFS_READ, Permission.TARIFFS_WRITE),
    ("/api/v1/webhooks", Permission.WEBHOOKS_READ, Permission.WEBHOOKS_WRITE),
)

EXACT_ROUTE_RULES: dict[str, str] = {
    "/api/v1/config": Permission.CONFIG_READ,
    "/api/v1/config/": Permission.CONFIG_READ,
    "/api/v1/billing/run-cycle": Permission.BILLING_FORCE,
}


def has_permission(role: str, permission: str) -> bool:
    """
    Проверка наличия права у роли.

    Args:
        role: Роль пользователя
        permission: Проверяемое право

    Returns:
        bool: Имеет ли роль указанное право
    """
    if role == Role.SUPER_ADMIN:
        return True
    perms = ROLE_PERMISSIONS.get(role, frozenset())
    return "*" in perms or permission in perms


def has_any_permission(permissions: list[str] | frozenset[str], required_permission: str | None) -> bool:
    """Check token permissions against a required permission."""
    if required_permission is None:
        return True
    return "*" in permissions or required_permission in permissions


def required_permission_for_route(path: str, method: str, user_id: str | None = None) -> str | None:
    """Return the permission required to access an API route.

    ``None`` means the route is authenticated but allowed to proceed. Controllers
    can still perform object-level checks, for example payment ownership.
    """
    normalized_path = path.rstrip("/") or path
    normalized_method = method.upper()

    exact_permission = EXACT_ROUTE_RULES.get(normalized_path) or EXACT_ROUTE_RULES.get(path)
    if exact_permission:
        return exact_permission

    if path.startswith("/api/v1/billing/demo") or path.startswith("/api/v1/services/demo"):
        return Permission.ABONENTS_READ

    if path.startswith("/api/v1/billing/"):
        if normalized_method not in READ_METHODS:
            return Permission.BILLING_WRITE
        return _self_scoped_permission(path, "/api/v1/billing", user_id, Permission.BILLING_READ)

    if path.startswith("/api/v1/services/"):
        if normalized_method not in READ_METHODS:
            return Permission.SERVICES_WRITE
        return _self_scoped_permission(path, "/api/v1/services", user_id, Permission.SERVICES_READ)

    if path.startswith("/api/v1/payments"):
        if normalized_method == "GET":
            return None
        if normalized_method == "POST" and normalized_path == "/api/v1/payments":
            return None
        if normalized_path.endswith("/refund"):
            return Permission.PAYMENTS_REFUND
        return Permission.PAYMENTS_WRITE

    for prefix, read_permission, write_permission in ADMIN_ROUTE_RULES:
        if path.startswith(prefix):
            return read_permission if normalized_method in READ_METHODS else write_permission

    return None


def _self_scoped_permission(path: str, prefix: str, user_id: str | None, fallback_permission: str) -> str | None:
    resource_id = path.removeprefix(prefix).strip("/").split("/", 1)[0]
    if not resource_id or not user_id:
        return fallback_permission
    try:
        UUID(resource_id)
    except ValueError:
        return fallback_permission
    return None if resource_id == user_id else fallback_permission
