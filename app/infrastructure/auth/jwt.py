# =============================================================================
# shm-next — JWT Authentication
# =============================================================================
"""
JWT-аутентификация.

Используется для генерации и валидации токенов доступа.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.api.config import AppConfig


@dataclass
class TokenPayload:
    """
    Полезная нагрузка JWT токена.

    Attributes:
        sub: Субъект (обычно ID пользователя)
        type: Тип токена (access или refresh)
        session_id: ID сессии
        permissions: Список прав
        exp: Время истечения (Unix timestamp)
        iat: Время создания (Unix timestamp)
        iss: Издатель
    """

    sub: str
    type: str  # "access" или "refresh"
    session_id: str
    permissions: list[str] = field(default_factory=list)
    exp: float = field(default_factory=lambda: datetime.now(UTC).timestamp())
    iat: float = field(default_factory=lambda: datetime.now(UTC).timestamp())
    iss: str = "shm-next"


class JWTManager:
    """
    Менеджер JWT токенов.

    Обеспечивает:
    - Создание access и refresh токенов
    - Декодирование и валидацию токенов
    - Проверку прав доступа
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        self._config = config or AppConfig()

    def create_access_token(
        self,
        subject: str,
        session_id: str,
        permissions: list[str] | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Создание access токена.

        Args:
            subject: Субъект (ID пользователя)
            session_id: ID сессии
            permissions: Список прав
            expires_delta: Время жизни (по умолчанию из конфига)

        Returns:
            str: JWT токен
        """
        if expires_delta is None:
            expires_delta = timedelta(
                minutes=self._config.access_token_expire_minutes
            )

        payload = TokenPayload(
            sub=subject,
            type="access",
            session_id=session_id,
            permissions=permissions or [],
            exp=(datetime.now(UTC) + expires_delta).timestamp(),
            iat=datetime.now(UTC).timestamp(),
        )

        return self._encode(payload)

    def create_refresh_token(
        self,
        subject: str,
        session_id: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Создание refresh токена.

        Args:
            subject: Субъект (ID пользователя)
            session_id: ID сессии
            expires_delta: Время жизни

        Returns:
            str: JWT refresh токен
        """
        if expires_delta is None:
            expires_delta = timedelta(days=self._config.refresh_token_expire_days)

        payload = TokenPayload(
            sub=subject,
            type="refresh",
            session_id=session_id,
            exp=(datetime.now(UTC) + expires_delta).timestamp(),
            iat=datetime.now(UTC).timestamp(),
        )

        return self._encode(payload)

    def decode(self, token: str) -> TokenPayload:
        """
        Декодирование токена.

        Args:
            token: JWT токен

        Returns:
            TokenPayload: Полезная нагрузка

        Raises:
            jwt.ExpiredSignatureError: Если токен истёк
            jwt.InvalidTokenError: Если токен невалиден
        """
        decoded = self._decode(token)
        return TokenPayload(**decoded)

    def _encode(self, payload: TokenPayload) -> str:
        """Кодирование payload в JWT."""
        return jwt.encode(
            {
                "sub": payload.sub,
                "type": payload.type,
                "session_id": payload.session_id,
                "permissions": payload.permissions,
                "exp": payload.exp,
                "iat": payload.iat,
                "iss": payload.iss,
            },
            self._config.secret_key,
            algorithm=self._config.algorithm,
        )

    def _decode(self, token: str) -> dict[str, Any]:
        """Декодирование JWT."""
        return jwt.decode(
            token,
            self._config.secret_key,
            algorithms=[self._config.algorithm],
            issuer="shm-next",
            options={
                "require": ["exp", "iat", "iss", "sub", "type", "session_id"],
            },
        )
