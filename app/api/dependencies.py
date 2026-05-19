# =============================================================================
# shm-next — API Dependencies
# =============================================================================
"""
Dependency providers for the Litestar application.

This module contains functions that provide dependencies to route handlers
via Litestar's dependency injection system.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from litestar.datastructures import State
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.config import get_app_config
from app.core.application.abonents.abonent_service import AbonentService
from app.core.application.billing.billing_service import BillingService
from app.core.application.payments.payment_service import PaymentService
from app.core.application.services.service_service import ServiceService
from app.core.application.tariffs.tariff_service import TariffService
from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.db.unit_of_work import UnitOfWork
from app.worker.brokers import broker


async def provide_db_session(state: State) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async database session.

    Args:
        state: Litestar application state containing the session maker.

    Yields:
        AsyncSession: Database session.
    """
    session_maker: async_sessionmaker[AsyncSession] = state.db_session_maker
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def provide_uow(session: AsyncSession) -> UnitOfWork:
    """
    Provide a UnitOfWork instance.

    Args:
        session: Async database session.

    Returns:
        UnitOfWork: Unit of work instance.
    """
    return UnitOfWork(session)


def provide_uow_dependency(state: State) -> UnitOfWork:
    """
    Provide a UnitOfWork instance for dependency injection.

    Args:
        state: Litestar application state containing the session maker.

    Returns:
        UnitOfWork: Unit of work instance.
    """
    session_maker = state.db_session_maker
    session = session_maker()
    return UnitOfWork(session)


def get_abonent_service(uow: UnitOfWork) -> AbonentService:
    """
    Provide an AbonentService instance.

    Args:
        uow: UnitOfWork instance.

    Returns:
        AbonentService: Abonent service instance.
    """
    from app.core.services.event_bus import EventBus
    return AbonentService(uow.abonents, EventBus())


def get_tariff_service(uow: UnitOfWork) -> TariffService:
    """
    Provide a TariffService instance.

    Args:
        uow: UnitOfWork instance.

    Returns:
        TariffService: Tariff service instance.
    """
    from app.core.application.tariffs.tariff_service import TariffService
    from app.core.services.event_bus import EventBus
    return TariffService(uow.tariffs, EventBus())


def get_service_service(uow: UnitOfWork) -> ServiceService:
    """
    Provide a ServiceService instance.

    Args:
        uow: UnitOfWork instance.

    Returns:
        ServiceService: Service service instance.
    """
    from app.core.application.services.service_service import ServiceService
    from app.core.services.event_bus import EventBus
    return ServiceService(uow.services, EventBus())


def get_payment_service(uow: UnitOfWork) -> PaymentService:
    """
    Provide a PaymentService instance.

    Args:
        uow: UnitOfWork instance.

    Returns:
        PaymentService: Payment service instance.
    """
    from app.core.application.payments.payment_service import PaymentService
    from app.core.services.event_bus import EventBus
    return PaymentService(uow.payments, uow.abonents, EventBus())


def get_billing_service(uow: UnitOfWork) -> BillingService:
    """
    Provide a BillingService instance.

    Args:
        uow: UnitOfWork instance.

    Returns:
        BillingService: Billing service instance.
    """
    from app.core.application.billing.billing_service import BillingService
    from app.core.services.billing_engine import BillingEngine
    from app.core.services.event_bus import EventBus
    return BillingService(
        uow.abonents,
        uow.billing,
        uow.services,
        uow.withdraws,
        EventBus(),
        BillingEngine(),
    )


_redis_cache: RedisCache | None = None


def get_redis() -> RedisCache:
    """
    Get or create a Redis cache instance.

    Returns:
        RedisCache: Redis cache instance.
    """
    global _redis_cache
    if _redis_cache is None:
        from app.api.config import AppConfig
        config = AppConfig()
        _redis_cache = RedisCache(redis_url=config.redis_url)
    return _redis_cache


def provide_redis() -> AsyncGenerator:
    """
    Provide a Redis client.

    Yields:
        RedisCache: Redis cache instance.
    """
    redis_client = get_redis()
    try:
        yield redis_client
    finally:
        # Close connection if needed
        pass


def provide_broker() -> AsyncGenerator:
    """
    Provide a Taskiq broker.

    Yields:
        Broker: Taskiq broker instance.
    """
    try:
        yield broker
    finally:
        # Close connection if needed
        pass


def provide_config() -> State:
    """
    Provide the application configuration.

    Returns:
        State: Litestar state with configuration.
    """
    config = get_app_config()
    state = State()
    state.config = config
    return state


# Dependency mappings for Litestar
dependencies = {
    "db_session": Provide(provide_db_session, sync_to_thread=False),
    "uow": Provide(provide_uow, sync_to_thread=False),
    "redis": Provide(provide_redis, sync_to_thread=False),
    "broker": Provide(provide_broker, sync_to_thread=False),
    "config": Provide(provide_config, sync_to_thread=False),
}
