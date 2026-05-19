# =============================================================================
# shm-next — Session Repository Protocol
# =============================================================================
"""Протокол репозитория сессий."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.entities.session import Session


class SessionRepositoryProtocol(ABC):
    """Протокол репозитория сессий."""

    @abstractmethod
    async def get(self, session_id: UUID) -> Session | None:
        """Получить сессию по ID."""
        ...

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> Session | None:
        """Получить сессию по хешу токена."""
        ...

    @abstractmethod
    async def get_active_by_abonent(self, abonent_id: UUID) -> list[Session]:
        """Получить активные сессии абонента."""
        ...

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Удалить истёкшие сессии. Возвращает количество удалённых."""
        ...

    @abstractmethod
    async def save(self, session: Session) -> Session:
        """Сохранить сессию."""
        ...
