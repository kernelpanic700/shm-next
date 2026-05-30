# =============================================================================
# shm-next - EventActionRule Entity
# =============================================================================
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4


class EventActionRule:
    """
    Правило создания внешнего действия по событию.

    Близко к SHM `events`: событие услуги выбирает действие, а результатом
    становится задача в spool для асинхронного выполнения.
    """

    def __init__(
        self,
        id: UUID | None = None,
        event_type: str = "",
        action_type: str = "",
        title: str | None = None,
        service_type: str | None = None,
        catalog_service_id: UUID | None = None,
        settings: dict | None = None,
        priority: int = 50,
        max_retries: int = 3,
        is_enabled: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
    ) -> None:
        self._id = id or uuid4()
        self._event_type = event_type
        self._action_type = action_type
        self._title = title or action_type
        self._service_type = service_type
        self._catalog_service_id = catalog_service_id
        self._settings = settings or {}
        self._priority = priority
        self._max_retries = max_retries
        self._is_enabled = is_enabled
        self._created_at = created_at or datetime.now(UTC)
        self._updated_at = updated_at or datetime.now(UTC)
        self._version = version
        self._validate()

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def event_type(self) -> str:
        return self._event_type

    @property
    def action_type(self) -> str:
        return self._action_type

    @property
    def title(self) -> str:
        return self._title

    @property
    def service_type(self) -> str | None:
        return self._service_type

    @property
    def catalog_service_id(self) -> UUID | None:
        return self._catalog_service_id

    @property
    def settings(self) -> dict:
        return dict(self._settings)

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def max_retries(self) -> int:
        return self._max_retries

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version

    def disable(self) -> None:
        self._is_enabled = False
        self._touch()

    def enable(self) -> None:
        self._is_enabled = True
        self._touch()

    def matches(
        self,
        event_type: str,
        service_type: str | None = None,
        catalog_service_id: UUID | None = None,
    ) -> bool:
        if not self._is_enabled or self._event_type != event_type:
            return False
        if self._service_type and self._service_type != service_type:
            return False
        if self._catalog_service_id and self._catalog_service_id != catalog_service_id:
            return False
        return True

    def _touch(self) -> None:
        self._updated_at = datetime.now(UTC)
        self._version += 1

    def _validate(self) -> None:
        if not self._event_type:
            raise ValueError("Event action rule event_type is required")
        if not self._action_type:
            raise ValueError("Event action rule action_type is required")
        if self._priority < 0:
            raise ValueError("Event action rule priority cannot be negative")
        if self._max_retries < 1:
            raise ValueError("Event action rule max_retries must be positive")
