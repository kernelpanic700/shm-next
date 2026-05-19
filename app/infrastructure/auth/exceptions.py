# =============================================================================
# shm-next — Auth Exceptions
# =============================================================================
"""Исключения модуля аутентификации."""

from __future__ import annotations


class AuthError(Exception):
    """Базовое исключение аутентификации."""
    pass


class InvalidCredentialsError(AuthError):
    """Неверные учётные данные."""
    pass


class TokenExpiredError(AuthError):
    """Токен истёк."""
    pass


class TokenInvalidError(AuthError):
    """Невалидный токен."""
    pass


class PermissionDeniedError(AuthError):
    """Недостаточно прав для выполнения операции."""
    pass
