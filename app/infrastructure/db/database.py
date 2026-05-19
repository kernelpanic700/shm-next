# =============================================================================
# shm-next — Database Initialization
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


def create_session_factory(
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    """
    Создание фабрики сессий.

    Args:
        engine: Движок SQLAlchemy (если None — создаётся новый)

    Returns:
        async_sessionmaker: Фабрика асинхронных сессий
    """
    if engine is None:
        engine = create_engine()

    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    return factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость для FastAPI/Litestar — получение сессии БД.

    Yields:
        AsyncSession: Сессия БД
    """
    engine = create_engine()
    async with engine.begin() as conn:
        session = async_sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with session() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise


async def init_db(drop: bool = False) -> None:
    """
    Инициализация базы данных.

    Создаёт все таблицы (или удаляет и заново создаёт при drop=True).

    Args:
        drop: Удалить существующие таблицы перед созданием
    """
    from sqlalchemy import text

    from app.infrastructure.db.models import Base

    engine = create_engine()

    async with engine.begin() as conn:
        if drop:
            # Отключаем проверку внешних ключей для безопасного удаления
            await conn.execute(text("SET session_replication_role = 'replica';"))
            await conn.run_sync(Base.metadata.drop_all)
            await conn.execute(text("SET session_replication_role = 'origin';"))

        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()


async def check_db_connection() -> bool:
    """
    Проверка подключения к базе данных.

    Returns:
        bool: True если подключение успешно
    """
    try:
        engine = create_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception:
        return False
