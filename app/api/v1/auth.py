# =============================================================================
# shm-next — API v1: Auth
# =============================================================================
"""Эндпоинты аутентификации и авторизации."""

from datetime import timedelta
from hmac import compare_digest
from typing import Any
from uuid import UUID, uuid4

from litestar import Controller, Request, get, post
from litestar.di import Provide
from litestar.datastructures import State
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_200_OK, HTTP_401_UNAUTHORIZED

from app.api.dependencies import provide_uow_dependency
from app.api.dto.requests import LoginRequest, RefreshTokenRequest, RegisterRequest
from app.api.dto.responses import AbonentResponse, ApiResponse, TokenResponse
from app.infrastructure.auth.jwt import JWTManager
from app.infrastructure.auth.password import hash_password, verify_password
from app.infrastructure.auth.permissions import Permission
from app.infrastructure.db.unit_of_work import UnitOfWork


def _get_jwt_manager(state: State) -> JWTManager:
    """Получить JWT менеджер из состояния приложения."""
    if not hasattr(state, "jwt_manager"):
        state.jwt_manager = JWTManager()
    return state.jwt_manager


def _is_bootstrap_admin_login(phone: str, password: str) -> bool:
    """Check optional env-configured admin credentials."""
    from app.api.config import get_app_config

    config = get_app_config()
    if not config.admin_phone or not compare_digest(phone, config.admin_phone):
        return False
    if config.admin_password_hash:
        return verify_password(password, config.admin_password_hash)
    return bool(config.admin_password) and compare_digest(password, config.admin_password)


class AuthController(Controller):
    path = "/auth"
    tags = ["Auth"]
    dependencies = {"uow": Provide(provide_uow_dependency)}

    @get(
        "/me",
        summary="Current abonent",
        description="Get current authenticated abonent profile",
        status_code=HTTP_200_OK,
    )
    async def me(
        self,
        request: Request,
        uow: UnitOfWork,
    ) -> ApiResponse:
        """Return the abonent identified by the access token."""
        user_id = request.scope.get("state", {}).get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        if str(user_id).startswith("admin:"):
            return ApiResponse(
                success=True,
                data={
                    "id": user_id,
                    "phone": str(user_id).removeprefix("admin:"),
                    "full_name": "Administrator",
                    "email": None,
                    "status": "ACTIVE",
                    "role": "admin",
                },
            )

        async with uow:
            abonent = await uow.abonents.get(UUID(str(user_id)))

        if abonent is None:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Authenticated abonent not found",
            )

        return ApiResponse(
            success=True,
            data=AbonentResponse.model_validate(abonent, from_attributes=True).model_dump(),
        )

    @post(
        "/login",
        summary="Вход в систему",
        description="Аутентификация абонента по телефону и паролю",
        status_code=HTTP_200_OK,
    )
    async def login(
        self,
        data: LoginRequest,
        uow: UnitOfWork,
        state: State,
    ) -> ApiResponse:
        """
        Аутентификация абонента.
        """
        from app.api.config import get_app_config

        config = get_app_config()
        jwt_manager = _get_jwt_manager(state)
        session_id = str(uuid4())

        if _is_bootstrap_admin_login(data.phone, data.password):
            access_token = jwt_manager.create_access_token(
                subject=f"admin:{data.phone}",
                session_id=session_id,
                permissions=["*"],
                expires_delta=timedelta(minutes=config.access_token_expire_minutes),
            )
            refresh_token = jwt_manager.create_refresh_token(
                subject=f"admin:{data.phone}",
                session_id=session_id,
                permissions=["*"],
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

        async with uow:
            abonent = await uow.abonents.get_by_phone(data.phone)

        if abonent is None or not verify_password(data.password, abonent.password_hash):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid phone or password",
            )

        access_token = jwt_manager.create_access_token(
            subject=str(abonent.id),
            session_id=session_id,
            permissions=[
                Permission.SELF_READ,
                Permission.SELF_WRITE,
            ],
            expires_delta=timedelta(minutes=config.access_token_expire_minutes),
        )

        refresh_token = jwt_manager.create_refresh_token(
            subject=str(abonent.id),
            session_id=session_id,
            permissions=[
                Permission.SELF_READ,
                Permission.SELF_WRITE,
            ],
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
        status_code=HTTP_200_OK,
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
        data: RegisterRequest,
        uow: UnitOfWork,
        state: State,
    ) -> ApiResponse:
        """
        Регистрация нового абонента.
        """
        from app.api.config import get_app_config
        from app.core.domain.entities.abonent import Abonent, AbonentStatus
        from app.core.domain.value_objects.money import Money

        config = get_app_config()

        async with uow:
            # Check if phone already exists
            existing = await uow.abonents.get_by_phone(data.phone)
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Phone number already registered",
                )

            password_hash = hash_password(data.password)

            # Create abonent
            abonent = Abonent(
                id=uuid4(),
                full_name=data.full_name,
                phone=data.phone,
                email=data.email,
                password_hash=password_hash,
                account_number=data.account_number or f"ACC{str(uuid4())[:8]}",
                balance=Money(0, "RUB"),
                status=AbonentStatus.ACTIVE,
            )

            await uow.abonents.save(abonent)

        return ApiResponse(
            success=True,
            data={
                "message": "Registration successful",
                "abonent_id": abonent.id,
                "account_number": abonent.account_number,
            },
        )
