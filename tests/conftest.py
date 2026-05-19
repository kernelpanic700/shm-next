# =============================================================================
# shm-next — Shared Test Fixtures
# =============================================================================
import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.infrastructure.db.models.base import Base


# Existing fixtures from the original conftest.py
@pytest.fixture
def event_bus():
    from app.core.services.event_bus import EventBus
    return EventBus()

@pytest.fixture
def billing_engine():
    from app.core.services.billing_engine import BillingEngine
    return BillingEngine(strategy="honest")

# Database fixtures with support for SQLite (default) and PostgreSQL (via TEST_DATABASE_URL)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if TEST_DATABASE_URL:
    # Use provided database URL (e.g., PostgreSQL for CI/CD)
    SQLALCHEMY_DATABASE_URL = TEST_DATABASE_URL
    ENGINE_OPTIONS = {
        "echo": False,
    }
else:
    # Default to SQLite in-memory for local development
    SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
        "echo": False,
    }

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Создаёт асинхронный engine для тестов."""
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        **ENGINE_OPTIONS
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncSession:
    """Создаёт новую сессию для каждого теста с автоматическим rollback."""
    async_session = async_sessionmaker(
        db_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()  # Откатываем все изменения после теста


@pytest_asyncio.fixture
async def uow(db_session):
    """Создаёт UnitOfWork для тестов."""
    from app.infrastructure.db.unit_of_work import UnitOfWork
    return UnitOfWork(db_session)
