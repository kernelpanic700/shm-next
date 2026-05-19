# =============================================================================
# shm-next — API v1: Auth
# =============================================================================
"""Эндпоинты аутентификации и авторизации."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import UUID

from litestar import Controller, post
from litestar.datastructures import State
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_401_UNAUTHORIZED

from app.api.dto.requests import LoginRequest, RefreshTokenRequest
from app.api.dto.responses import ApiResponse, TokenResponse
from app.infrastructure.auth.jwt import JWTManager


def _get_jwt_manager(state: State) -> JWTManager:
    """Получить JWT менеджер из состояния приложения."""
    if not hasattr(state, "jwt_manager"):
        state.jwt_manager = JWTManager()
    return state.jwt_manager


class AuthController(Controller):
    path = "/v1/auth"
    tags = ["Auth"]

    @post(
        "/login",
        summary="Вход в систему",
        description="Аутентификация абонента по телефону и паролю",
    )
    async def login(
        self,
        data: LoginRequest,
        state: State,
    ) -> ApiResponse:
        """
        Аутентификация абонента.

        В реальной реализации:
        1. Проверка пароля через хэш (bcrypt/argon2)
        2. Проверка статуса абонента
        3. Создание сессии
        4. Генерация JWT токенов
        """
        from app.api.config import get_app_config
        from app.infrastructure.db.database import create_engine, create_session_factory
        from app.infrastructure.db.repositories.abonent_repo import AbonentRepository

        config = get_app_config()
        engine = create_engine(config.database_url)
        factory = create_session_factory(engine)

        async with factory() as session:
            async with session.begin():
                repo = AbonentRepository(session)
                abonent = await repo.get_by_phone(data.phone)

                if not abonent:
                    raise HTTPException(
                        status_code=HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials",
                    )

                # TODO: verify password hash
                # if not bcrypt.checkpw(data.password.encode(), abonent.password_hash.encode()):
                #     raise HTTPException(...)

                if abonent.status.value not in ("ACTIVE",):
                    raise HTTPException(
                        status_code=HTTP_401_UNAUTHORIZED,
                        detail="Account is not active",
                    )

                jwt_manager = _get_jwt_manager(state)
                session_id = str(UUID())

                access_token = jwt_manager.create_access_token(
                    subject=str(abonent.id),
                    session_id=session_id,
                    permissions=["abonent:read", "billing:read", "payments:read"],
                    expires_delta=timedelta(minutes=config.access_token_expire_minutes),
                )

                refresh_token = jwt_manager.create_refresh_token(
                    subject=str(abonent.id),
                    session_id=session_id,
                    expires_delta=timedelta(days=config.refresh_token_expire_days),
                )

                return ApiResponse(
                    success=True,
                    data=TokenResponse(
                        access_token=access_token,
                        refresh_token=refresh_token,
                        expires_in=config.access_token_expire_minutes * 60,
                    ).model_dump(),
                )

    @post(
        "/refresh",
        summary="Обновление токена",
        description="Получение нового access-токена по refresh-токену",
    )
    async def refresh(
        self,
        data: RefreshTokenRequest,
        state: State,
    ) -> ApiResponse:
        """Обновление access-токена."""
        jwt_manager = _get_jwt_manager(state)

        try:
            payload = jwt_manager.decode(data.refresh_token)
        except Exception:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if payload.type != "refresh":
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        from app.api.config import get_app_config
        config = get_app_config()

        new_access_token = jwt_manager.create_access_token(
            subject=payload.sub,
            session_id=payload.session_id,
            permissions=payload.permissions,
        )

        return ApiResponse(
            success=True,
            data=TokenResponse(
                access_token=new_access_token,
                refresh_token=data.refresh_token,
                expires_in=config.access_token_expire_minutes * 60,
            ).model_dump(),
        )

    @post(
        "/register",
        summary="Регистрация",
        description="Регистрация нового абонента",
        status_code=201,
    )
    async def register(
        self,
        data: Any,  # AbonentCreate + password
        state: State,
    ) -> ApiResponse:
        """
        Регистрация нового абонента.

        В реальной реализации:
        1. Валидация данных
        2. Хэширование пароля
        3. Создание абонента
        4. Отправка подтверждения (email/SMS)
        """
        # TODO: implement full registration flow
        return ApiResponse(
            success=True,
            data={"message": "Registration endpoint — TODO"},
        )
