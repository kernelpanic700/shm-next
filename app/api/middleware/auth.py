# =============================================================================
# shm-next — Auth Middleware
# =============================================================================
"""
Middleware аутентификации и авторизации.

Проверяет JWT-токен в заголовке Authorization и устанавливает
current_user в state запроса.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from litestar import Request, Response, status_codes
from litestar.exceptions import HTTPException
from litestar.middleware.base import AbstractMiddleware

from app.infrastructure.auth.exceptions import AuthError


class AuthMiddleware(AbstractMiddleware):
    """
    Middleware аутентификации.

    Пропускает пути без авторизации (health, docs, auth endpoints).
    Для защищённых путей проверяет JWT и устанавливает current_user.
    """

    # Пути, не требующие аутентификации
    PUBLIC_PATHS = {
        "/api/health",
        "/api/docs",
        "/api/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/admin/login",
    }

    def __init__(
        self,
        app,
        *,
        exclude: set[str] | None = None,
    ):
        super().__init__(app)
        self._exclude = exclude or set()

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        # Пропускаем публичные пути
        if request.url.path in self.PUBLIC_PATHS or request.url.path in self._exclude:
            return await call_next(request)

        # Извлекаем токен
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status_codes.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header",
            )

        token = auth_header[7:]  # Убираем "Bearer "

        try:
            jwt_manager = request.app.state.jwt_manager
            payload = jwt_manager.decode(token)

            # Проверяем тип токена
            if payload.type != "access":
                raise HTTPException(
                    status_code=status_codes.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )

            # Устанавливаем пользователя в state
            request.state.user_id = payload.sub
            request.state.session_id = payload.session_id
            request.state.permissions = payload.permissions

        except AuthError as exc:
            raise HTTPException(
                status_code=status_codes.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            )
        except Exception:
            raise HTTPException(
                status_code=status_codes.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed",
            )

        return await call_next(request)


class AdminMiddleware(AbstractMiddleware):
    """
    Middleware для админ-панели.

    Проверяет наличие admin-роли у пользователя.
    """

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        user_id = getattr(request.state, "user_id", None)
        permissions = getattr(request.state, "permissions", [])

        if not user_id:
            raise HTTPException(
                status_code=status_codes.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        if "admin" not in permissions and "*" not in permissions:
            raise HTTPException(
                status_code=status_codes.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

        return await call_next(request)
