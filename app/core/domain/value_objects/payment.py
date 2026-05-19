# =============================================================================
# shm-next — Payment Status
# =============================================================================
from __future__ import annotations

from enum import Enum


class PaymentStatus(Enum):
    """Статусы платежа."""
    NEW = "NEW"              # Новый
    PENDING = "PENDING"      # Ожидает обработки
    PROCESSING = "PROCESSING"  # В обработке
    COMPLETED = "COMPLETED"  # Завершён
    FAILED = "FAILED"        # Ошибка
    REFUNDED = "REFUNDED"    # Возвращён
    CANCELLED = "CANCELLED"  # Отменён
