# =============================================================================
# shm-next — Spool Status
# =============================================================================
from __future__ import annotations

from enum import Enum


class SpoolStatus(Enum):
    """Статусы задачи внешнего действия."""
    NEW = "NEW"              # Новая
    PENDING = "PENDING"      # Ожидает выполнения
    PROCESSING = "PROCESSING"  # Выполняется
    SUCCESS = "SUCCESS"      # Успешно
    FAILED = "FAILED"        # Ошибка (можно ретраить)
    STUCK = "STUCK"          # В DLQ (исчерпаны попытки)
    DELAYED = "DELAYED"      # Отложена (circuit breaker)
    CANCELLED = "CANCELLED"  # Отменена
