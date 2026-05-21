# =============================================================================
# shm-next — Database Initialization
#
# =============================================================================
"""
Инициализация и настройка подключения к PostgreSQL.

Используется asyncpg через SQLAlchemy 2.0 async.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.config import AppConfig


def create_engine(dsn: str | None = None) -> AsyncEngine:
    """
    Создание асинхронного движка SQLAlchemy.

    Args:
        dsn: Строка подключения (если None — берётся из конфига)

    Returns:
        AsyncEngine: Движок SQLAlchemy
    """

    if dsn is None:
        config = AppConfig()
        dsn = config.database_url

    engine = create_async_engine(
        dsn,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    return engine


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Создание фабрики сессий.

    Args:
        engine: Движок SQLAlchemy

    Returns:
        async_sessionmaker: Фабрика асинхронных сессий
    """
    return async_sessionmaker(engine, expire_on_commit=False)


def get_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    """
    Контекстный менеджер для получения сессии.

    Args:
        session_factory: Фабрика сессий

    Yields:
        AsyncSession: Асинхронная сессия
    """
    async with session_factory() as session:
        yield session
