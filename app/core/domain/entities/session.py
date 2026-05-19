# =============================================================================
# shm-next — Session Entity
# =============================================================================
"""
Сессия абонента.

Отслеживает активные сессии авторизации абонентов.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4


class Session:
    """
    Сессия авторизации абонента.

    Attributes:
        id: Идентификатор сессии.
        abonent_id: ID абонента.
        token_hash: Хеш токена авторизации.
        ip_address: IP-адрес, с которого создана сессия.
        user_agent: User-Agent клиента.
        expires_at: Время истечения сессии.
        is_active: Активна ли сессия.
    """

    def __init__(
        self,
        id: UUID | None = None,
        abonent_id: UUID | None = None,
        token_hash: str = "",
        ip_address: str | None = None,
        user_agent: str | None = None,
        expires_at: datetime | None = None,
        is_active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
    ) -> None:
        self._id = id or uuid4()
        self._abonent_id = abonent_id
        self._token_hash = token_hash
        self._ip_address = ip_address
        self._user_agent = user_agent
        self._expires_at = expires_at  # Keep None if not provided
        self._is_active = is_active
        self._created_at = created_at or datetime.now(UTC)
        self._updated_at = updated_at or datetime.now(UTC)
        self._version = version

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def abonent_id(self) -> UUID | None:
        return self._abonent_id

    @property
    def token_hash(self) -> str:
        return self._token_hash

    @property
    def ip_address(self) -> str | None:
        return self._ip_address

    @property
    def user_agent(self) -> str | None:
        return self._user_agent

    @property
    def expires_at(self) -> datetime | None:
        return self._expires_at

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version

    # ------------------------------------------------------------------
    # Business methods
    # ------------------------------------------------------------------

    def is_expired(self, at: datetime | None = None) -> bool:
        """Проверяет, истекла ли сессия."""
        check_date = at or datetime.now(UTC)
        if self._expires_at is None:
            return False
        return check_date > self._expires_at

    def verify_token(self, token: str) -> bool:
        """
        Проверяет соответствие переданного токена хешу сессии.

        Использует безопасное сравнение для предотвращения timing attacks.
        """
        import hashlib
        import hmac

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return hmac.compare_digest(token_hash, self._token_hash)

    def expire(self) -> None:
        """Принудительно завершить сессию."""
        self._is_active = False
        self._updated_at = datetime.now(UTC)
        self._version += 1
