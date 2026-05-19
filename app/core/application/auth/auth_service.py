# =============================================================================
# shm-next — Auth Application Service
# =============================================================================
"""
Application Service для аутентификации и авторизации.
"""

from __future__ import annotations

from uuid import uuid4

import structlog

from app.core.application.abonents.abonent_service import AbonentService
from app.infrastructure.auth.exceptions import (
    InvalidCredentialsError,
    TokenInvalidError,
)
from app.infrastructure.auth.jwt import JWTManager, TokenPayload

logger = structlog.get_logger("auth_service")


class AuthService:
    """
    Сервис аутентификации.

    Use Cases:
    - Вход по телефону и паролю
    - Обновление токена
    - Проверка токена
    """

    def __init__(
        self,
        abonent_service: AbonentService,
        jwt_manager: JWTManager,
    ) -> None:
        self._abonent_service = abonent_service
        self._jwt_manager = jwt_manager

    async def login(
        self,
        phone: str,
        password: str,
    ) -> tuple[TokenPayload, TokenPayload]:
        """
        Вход в систему.

        Args:
            phone: Телефон
            password: Пароль

        Returns:
            tuple: (access_token_payload, refresh_token_payload)

        Raises:
            InvalidCredentialsError: Если учётные данные неверны
        """
        # NOTE: В реальном приложении здесь проверка хеша пароля
        # Для демо используем упрощённую проверку
        import hashlib


        # Ищем абонента по телефону
        # В реальности пароль проверяется через bcrypt
        abonent = await self._abonent_service._abonent_repo.get_by_phone(phone)

        if abonent is None:
            raise InvalidCredentialsError("Invalid phone or password")

        # Простая проверка для демо (в продакшене — bcrypt)
        password_hash = hashlib.sha256(
            (password + abonent.phone).encode()
        ).hexdigest()

        stored_hash = hashlib.sha256(
            ("demo_password" + abonent.phone).encode()
        ).hexdigest()

        if password_hash != stored_hash and password != "demo":
            raise InvalidCredentialsError("Invalid phone or password")

        # Создаём сессию
        session_id = str(uuid4())

        # Генерируем токены
        access_payload = self._jwt_manager.create_access_token(
            subject=str(abonent.id),
            session_id=session_id,
            permissions=["abonent:read", "abonent:write"],
        )

        refresh_payload = self._jwt_manager.create_refresh_token(
            subject=str(abonent.id),
            session_id=session_id,
        )

        logger.info(
            "User logged in",
            abonent_id=abonent.id,
            phone=phone,
        )

        return access_payload, refresh_payload

    async def refresh_tokens(
        self,
        refresh_token: str,
    ) -> tuple[TokenPayload, TokenPayload]:
        """
        Обновить токены.

        Args:
            refresh_token: Refresh токен

        Returns:
            tuple: (new_access_payload, new_refresh_payload)

        Raises:
            TokenExpiredError: Если refresh токен истёк
            TokenInvalidError: Если токен невалиден
        """
        try:
            payload = self._jwt_manager.decode(refresh_token)
        except Exception as exc:
            raise TokenInvalidError("Invalid refresh token") from exc

        if payload.type != "refresh":
            raise TokenInvalidError("Not a refresh token")

        # Создаём новую сессию
        session_id = str(uuid4())

        access_payload = self._jwt_manager.create_access_token(
            subject=payload.sub,
            session_id=session_id,
        )

        refresh_payload = self._jwt_manager.create_refresh_token(
            subject=payload.sub,
            session_id=session_id,
        )

        return access_payload, refresh_payload

    async def validate_token(self, token: str) -> TokenPayload:
        """
        Валидировать access токен.

        Args:
            token: JWT токен

        Returns:
            TokenPayload: Полезная нагрузка

        Raises:
            TokenExpiredError: Если токен истёк
            TokenInvalidError: Если токен невалиден
        """
        try:
            payload = self._jwt_manager.decode(token)
        except Exception as exc:
            raise TokenInvalidError("Invalid token") from exc

        if payload.type != "access":
            raise TokenInvalidError("Not an access token")

        return payload
