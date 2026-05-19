# =============================================================================
# shm-next — SpoolTask Entity
# =============================================================================
from __future__ import annotations

from datetime import UTC, datetime

from app.core.domain.value_objects import SpoolStatus


class SpoolTask:
    """
    Задача внешнего действия (Spool).

    Используется для отложенного выполнения внешних действий:
    - Отправка уведомлений
    - Вызов NAS-команд
    - Webhook-вызовы
    - Интеграции с внешними системами
    """

    def __init__(
        self,
        id: int | None = None,
        action_type: str = "",
        payload: dict | None = None,
        priority: int = 50,
        status: str = SpoolStatus.NEW,
        max_retries: int = 3,
        retry_count: int = 0,
        worker_id: str | None = None,
        execute_after: datetime | None = None,
        result: dict | None = None,
        error_message: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
    ) -> None:
        self._id = id
        self._action_type = action_type
        self._payload = payload or {}
        self._priority = priority
        self._status = status
        self._max_retries = max_retries
        self._retry_count = retry_count
        self._worker_id = worker_id
        self._execute_after = execute_after
        self._result = result
        self._error_message = error_message
        self._created_at = created_at or datetime.now(UTC)
        self._updated_at = updated_at or datetime.now(UTC)
        self._version = version

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def action_type(self) -> str:
        return self._action_type

    @property
    def payload(self) -> dict:
        return self._payload

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def status(self) -> str:
        return self._status

    @property
    def max_retries(self) -> int:
        return self._max_retries

    @property
    def retry_count(self) -> int:
        return self._retry_count

    @property
    def worker_id(self) -> str | None:
        return self._worker_id

    @property
    def execute_after(self) -> datetime | None:
        return self._execute_after

    @property
    def result(self) -> dict | None:
        return self._result

    @property
    def error_message(self) -> str | None:
        return self._error_message

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version

    def mark_processing(self, worker_id: str) -> None:
        self._status = SpoolStatus.PROCESSING
        self._worker_id = worker_id
        self._updated_at = datetime.now(UTC)

    def mark_success(self, result: dict | None = None) -> None:
        self._status = SpoolStatus.SUCCESS
        self._result = result
        self._updated_at = datetime.now(UTC)

    def mark_failed(self, error: str) -> None:
        self._retry_count += 1
        self._error_message = error

        if self._retry_count >= self._max_retries:
            self._status = SpoolStatus.STUCK
        else:
            self._status = SpoolStatus.FAILED

        self._updated_at = datetime.now(UTC)
