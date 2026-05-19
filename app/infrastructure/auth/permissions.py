# =============================================================================
# shm-next — Permissions System
# =============================================================================
"""
Система прав доступа (RBAC + ABAC).

Определяет роли и разрешения для различных операций.
"""

from __future__ import annotations


class Role:
    """Роли пользователей."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    ABONENT = "abonent"


class Permission:
    """Разрешения системы."""
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
        Permission.SPOOL_READ,
        Permission.CONFIG_READ,
    ]),
    Role.OPERATOR: frozenset([
        Permission.ABONENTS_READ,
        Permission.BILLING_READ,
        Permission.PAYMENTS_READ,
        Permission.SPOOL_READ,
    ]),
    Role.ABONENT: frozenset([
        Permission.BILLING_READ,
        Permission.PAYMENTS_READ,
    ]),
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
