# =============================================================================
# shm-next — Withdraw Status
# =============================================================================
from __future__ import annotations

from enum import Enum


class WithdrawStatus(Enum):
    """Статусы списания."""
    NEW = "NEW"              # Новое
    PENDING = "PENDING"      # Ожидает выполнения
    PROCESSING = "PROCESSING"  # В обработке
    COMPLETED = "COMPLETED"  # Завершено
    FAILED = "FAILED"        # Ошибка
    CANCELLED = "CANCELLED"  # Отменено

    def is_terminal(self) -> bool:
        return self in (WithdrawStatus.COMPLETED, WithdrawStatus.FAILED, WithdrawStatus.CANCELLED)

    def can_retry(self) -> bool:
        return self in (WithdrawStatus.FAILED, WithdrawStatus.PENDING)
