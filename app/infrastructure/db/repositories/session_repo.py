# =============================================================================
# shm-next — Session Repository
# =============================================================================
"""Репозиторий сессий."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.entities.session import Session
from app.core.domain.repositories.session import SessionRepositoryProtocol
from app.infrastructure.db.models import SessionModel


class SessionRepository(SessionRepositoryProtocol):
    """Репозиторий сессий."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, session_id: UUID) -> Session | None:
        """Получить сессию по ID."""
        model = await self._session.get(SessionModel, session_id)
        return self._to_domain(model) if model else None

    async def get_by_token_hash(self, token_hash: str) -> Session | None:
        """Получить сессию по хешу токена."""
        stmt = select(SessionModel).where(
            SessionModel.token_hash == token_hash
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_active_by_abonent(self, abonent_id: UUID) -> list[Session]:
        """Получить активные сессии абонента."""
        stmt = select(SessionModel).where(
            SessionModel.abonent_id == abonent_id,
            SessionModel.is_active,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def cleanup_expired(self) -> int:
        """Удалить истёкшие сессии. Возвращает количество удалённых."""

        now = datetime.now(UTC)
        stmt = delete(SessionModel).where(
            SessionModel.expires_at < now,
            SessionModel.is_active,
        )
        result = await self._session.execute(stmt)
        return result.rowcount

    async def save(self, session: Session) -> Session:
        """Сохранить сессию."""
        # Check if model exists
        existing = await self._session.get(SessionModel, session.id)
        if existing:
            # Update existing
            existing.abonent_id = session.abonent_id
            existing.token_hash = session.token_hash
            existing.ip_address = session.ip_address
            existing.user_agent = session.user_agent
            existing.expires_at = session.expires_at
            existing.is_active = session.is_active
            existing.version = session.version
            model = existing
        else:
            # Create new
            model = SessionModel(
                id=session.id,
                abonent_id=session.abonent_id,
                token_hash=session.token_hash,
                ip_address=session.ip_address,
                user_agent=session.user_agent,
                expires_at=session.expires_at,
                is_active=session.is_active,
                version=session.version,
            )
            self._session.add(model)

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: SessionModel) -> Session:
        """Конвертация модели в доменную сущность."""
        expires_at = model.expires_at
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        return Session(
            id=model.id,
            abonent_id=model.abonent_id,
            token_hash=model.token_hash,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            expires_at=expires_at,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )
