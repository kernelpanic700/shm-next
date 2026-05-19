# =============================================================================
# shm-next — API Middleware
# =============================================================================
"""
Custom middleware for the Litestar application.

Includes authentication, logging, and other cross-cutting concerns.
"""

from __future__ import annotations

import time

from litestar import Request
from litestar.enums import ScopeType
from litestar.middleware import DefineMiddleware
from litestar.middleware.authentication import AuthenticationMiddleware
from litestar.middleware.base import AbstractMiddleware
from litestar.security.jwt import JWTAuth, Token
from litestar.types import Message, Receive, Scope, Send

from app.api.auth import authenticate_user
from app.api.config import get_app_config
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


def auth_middleware() -> DefineMiddleware[None]:
    """
    Create authentication middleware using JWT.

    Returns:
        DefineMiddleware: Configured authentication middleware.
    """
    config = get_app_config()

    jwt_auth = JWTAuth[Token, dict, str](
        token=Token,
        retrieve_user_handler=authenticate_user,
        secret=config.secret_key,
        algorithm=config.algorithm,
    )

    return DefineMiddleware(AuthenticationMiddleware, auth=jwt_auth, exclude=["/docs", "/schema", "/openapi.json", "/health"])


class LoggingMiddleware(AbstractMiddleware):
    """
    Middleware for logging requests and responses.
    """

    async def send_wrapper(self, scope: Scope, send: Send, start_time: float, request: Request) -> Send:
        async def wrapped_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                process_time = time.time() - start_time
                logger.info(
                    "Request completed",
                    method=request.method,
                    path=request.url.path,
                    status_code=message["status"],
                    process_time=round(process_time, 4),
                )
            await send(message)
        return wrapped_send

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in (ScopeType.HTTP, ScopeType.WEBSOCKET):
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        start_time = time.time()

        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query),
            client=request.client.host if request.client else None,
        )

        wrapped_send = await self.send_wrapper(scope, send, start_time, request)
        await self.app(scope, receive, wrapped_send)


def logging_middleware() -> DefineMiddleware[None]:
    """
    Create logging middleware.

    Returns:
        DefineMiddleware: Configured logging middleware.
    """
    return DefineMiddleware(LoggingMiddleware)


class TimingMiddleware(AbstractMiddleware):
    """
    Middleware for adding timing headers to responses.
    """

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] not in (ScopeType.HTTP, ScopeType.WEBSOCKET):
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                process_time = time.time() - start_time
                headers = dict(message.get("headers", []))
                headers[b"x-process-time"] = str(process_time).encode()
                message["headers"] = list(headers.items())
            await send(message)

        await self.app(scope, receive, send_wrapper)


def timing_middleware() -> DefineMiddleware[None]:
    """
    Create timing middleware.

    Returns:
        DefineMiddleware: Configured timing middleware.
    """
    return DefineMiddleware(TimingMiddleware)


# Middleware stack
def make_middleware() -> list[DefineMiddleware[None]]:
    """
    Create the complete middleware stack.

    Returns:
        list[DefineMiddleware]: List of middleware components.
    """
    return [
        timing_middleware(),
        auth_middleware(),
    ]
