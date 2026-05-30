# =============================================================================
# shm-next — Auth Middleware
# =============================================================================
"""
Middleware аутентификации и авторизации.

Проверяет JWT-токен в заголовке Authorization и устанавливает
current_user в state запроса.
"""

from __future__ import annotations

import json

from litestar import status_codes
from litestar.middleware.base import ASGIMiddleware
from litestar.types import ASGIApp, Receive, Scope, Send

from app.api.config import get_app_config
from app.infrastructure.auth.exceptions import AuthError
from app.infrastructure.auth.jwt import JWTManager
from app.infrastructure.auth.permissions import has_any_permission, required_permission_for_route


class AuthMiddleware(ASGIMiddleware):
    """
    Middleware аутентификации.

    Пропускает пути без авторизации (health, docs, auth endpoints).
    Для защищённых путей проверяет JWT и устанавливает current_user.
    """

    # Пути, не требующие аутентификации
    PUBLIC_PATHS = {
        "/health",
        "/api/health",
        "/api/v1/health",
        "/api/v1/health/",
        "/api/v1/health/db",
        "/api/v1/config/health",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
    }

    PUBLIC_PREFIXES = (
        "/schema",
        "/docs",
        "/api/docs",
        "/api/openapi",
    )

    def __init__(
        self,
        exclude: set[str] | None = None,
    ):
        self._exclude = exclude or set()
        self._jwt_manager = JWTManager(get_app_config())

    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        path = scope.get("path", "")
        method = scope.get("method", "")
        if self._is_public_path(path) or method == "OPTIONS":
            await next_app(scope, receive, send)
            return

        auth_header = self._get_authorization_header(scope)
        if not auth_header or not auth_header.startswith("Bearer "):
            await self._send_error(
                scope,
                receive,
                send,
                status_codes.HTTP_401_UNAUTHORIZED,
                "Missing or invalid authorization header",
            )
            return

        token = auth_header[7:]

        try:
            payload = self._jwt_manager.decode(token)

            if payload.type != "access":
                await self._send_error(scope, receive, send, status_codes.HTTP_401_UNAUTHORIZED, "Invalid token type")
                return

            state = scope.setdefault("state", {})
            state["user_id"] = payload.sub
            state["session_id"] = payload.session_id
            state["permissions"] = payload.permissions

            required_permission = required_permission_for_route(path, method, payload.sub)
            if not has_any_permission(payload.permissions, required_permission):
                await self._send_error(scope, receive, send, status_codes.HTTP_403_FORBIDDEN, "Permission denied")
                return

        except AuthError as exc:
            await self._send_error(scope, receive, send, status_codes.HTTP_401_UNAUTHORIZED, str(exc))
            return
        except Exception:
            await self._send_error(scope, receive, send, status_codes.HTTP_401_UNAUTHORIZED, "Token validation failed")
            return

        await next_app(scope, receive, send)

    def _is_public_path(self, path: str) -> bool:
        return (
            path in self.PUBLIC_PATHS
            or path in self._exclude
            or any(path.startswith(prefix) for prefix in self.PUBLIC_PREFIXES)
        )

    @staticmethod
    def _get_authorization_header(scope: Scope) -> str | None:
        for key, value in scope.get("headers", []):
            if key.lower() == b"authorization":
                return value.decode("latin-1")
        return None

    @staticmethod
    async def _send_error(scope: Scope, receive: Receive, send: Send, status_code: int, detail: str) -> None:
        body = json.dumps(
            {
                "success": False,
                "error": {
                    "code": status_code,
                    "message": detail,
                },
            }
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
                "more_body": False,
            }
        )
