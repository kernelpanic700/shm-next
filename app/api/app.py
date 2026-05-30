# =============================================================================
# shm-next — Main Application
# =============================================================================
"""
Точка входа приложения Litestar.

Создаёт и конфигурирует ASGI-приложение со всеми зависимостями.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.exceptions import HTTPException
from litestar.openapi import OpenAPIConfig
from litestar import Response
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR

from app.api.config import get_app_config
from app.api.middleware.auth import AuthMiddleware
from app.api.v1 import create_v1_router
from app.infrastructure.db.database import create_engine, create_session_factory
from app.infrastructure.observability.logging import setup_logging


def http_exception_handler(request, exc: HTTPException) -> Response:
    """Global exception handler for HTTP exceptions."""
    return Response(
        content={
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
            },
        },
        status_code=exc.status_code,
    )


def generic_exception_handler(request, exc: Exception) -> Response:
    """Global exception handler for unexpected exceptions."""
    import traceback
    import logging
    logger = logging.getLogger(__name__)

    # Log the full traceback for debugging
    logger.error(f"Exception in request: {exc}\n{traceback.format_exc()}")

    # In debug mode, include the actual error message
    config = get_app_config()
    if config.debug:
        return Response(
            content={
                "success": False,
                "error": {
                    "code": HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                },
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        content={
            "success": False,
            "error": {
                "code": HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error",
            },
        },
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
    )


def domain_exception_handler(request, exc: Exception) -> Response:
    """Global exception handler for domain exceptions."""
    import traceback
    import logging
    logger = logging.getLogger(__name__)

    # Log the full traceback for debugging
    logger.error(f"Exception in request: {exc}\n{traceback.format_exc()}")

    from app.core.domain.exceptions import (
        DomainError,
        InsufficientBalanceError,
        ObjectNotFoundError,
        ServiceNotActiveError,
    )

    if isinstance(exc, InsufficientBalanceError):
        return Response(
            content={
                "success": False,
                "error": {
                    "code": 400,
                    "message": exc.message,
                    "type": "insufficient_balance",
                    "required": exc.required,
                    "available": exc.available,
                    "currency": exc.currency,
                },
            },
            status_code=400,
        )
    elif isinstance(exc, ServiceNotActiveError):
        return Response(
            content={
                "success": False,
                "error": {
                    "code": 400,
                    "message": exc.message,
                    "type": "service_not_active",
                    "service_id": exc.service_id,
                },
            },
            status_code=400,
        )
    elif isinstance(exc, ObjectNotFoundError):
        return Response(
            content={
                "success": False,
                "error": {
                    "code": 404,
                    "message": exc.message,
                    "type": "object_not_found",
                    "object_type": exc.object_type,
                    "object_id": exc.object_id,
                },
            },
            status_code=404,
        )
    elif isinstance(exc, DomainError):
        return Response(
            content={
                "success": False,
                "error": {
                    "code": 400,
                    "message": exc.message,
                    "type": "domain_error",
                },
            },
            status_code=400,
        )

    # Fallback to generic handler
    return generic_exception_handler(request, exc)


exception_handlers = {
    HTTPException: http_exception_handler,
    Exception: domain_exception_handler,
}


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    """
    Управление жизненным циклом приложения.

    Startup:
    - Инициализация подключения к БД
    - Инициализация Redis-кэша
    - Настройка логирования

    Shutdown:
    - Закрытие подключений
    """
    config = get_app_config()

    # === Startup ===
    setup_logging()

    # Создаём движок БД
    engine = create_engine(config.database_url)
    session_factory = create_session_factory(engine)

    # Создаём Redis-клиент (optional)
    cache = None
    try:
        from app.infrastructure.cache.redis_cache import RedisCache
        cache = RedisCache(config.redis_url)
        await cache.ping()
    except Exception:
        pass  # Redis optional in dev

    # Сохраняем в состояние приложения
    app.state.database_engine = engine
    app.state.session_factory = session_factory
    app.state.db_session_maker = session_factory
    app.state.cache = cache

    # Инициализация Taskiq брокера (optional)
    broker = None
    try:
        from app.infrastructure.queue.tasks import create_broker
        broker = create_broker()
    except Exception:
        pass  # Broker optional in dev
    app.state.taskiq_broker = broker

    # Инициализация spool репозитория
    from app.infrastructure.db.repositories.spool_repo import SpoolTaskRepository
    spool_repo = SpoolTaskRepository(session_factory())
    app.state.spool_repo = spool_repo

    yield

    # === Shutdown ===
    if cache:
        await cache.close()
    await engine.dispose()


def create_application() -> Litestar:
    """
    Фабрика создания приложения Litestar.

    Returns:
        Litestar: Сконфигурированное ASGI-приложение
    """
    config = get_app_config()

    # CORS
    cors_config = CORSConfig(
        allow_origins=config.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # OpenAPI
    openapi_config = OpenAPIConfig(
        title="SHM Next API",
        version="3.0.0",
        description="""
        # SHM Next — API документация

        Система управления абонентами нового поколения.

        ## Архитектура
        - **Domain Layer** — доменные сущности, value objects, события
        - **Application Layer** — use cases, application services
        - **Infrastructure Layer** — БД, кэш, очереди, внешние сервисы
        - **API Layer** — HTTP-эндпоинты (REST)
        """,
        create_examples=True,
    )

    # Health endpoint
    @get("/health", summary="Health check")
    async def health_check() -> dict:
        return {"status": "healthy"}

    # Создаём роутер
    v1_router = create_v1_router()

    app = Litestar(
        route_handlers=[health_check, v1_router],
        cors_config=cors_config,
        openapi_config=openapi_config,
        middleware=[AuthMiddleware()],
        lifespan=[lifespan],
        debug=config.debug,
        exception_handlers=exception_handlers,
    )

    return app


# Глобальный экземпляр приложения
app = create_application()


if __name__ == "__main__":
    import uvicorn

    config = get_app_config()
    uvicorn.run(
        "app.api.app:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.reload,
        workers=config.workers,
        log_level=config.log_level.lower(),
    )
