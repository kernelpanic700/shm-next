# =============================================================================
# shm-next — Service Status
# =============================================================================
from __future__ import annotations

from enum import StrEnum


class ServiceStatus(StrEnum):
    """Статусы услуги абонента."""
    INIT = "INIT"           # Инициализация
    ACTIVE = "ACTIVE"       # Активна
    PROGRESS = "PROGRESS"   # В процессе активации
    DEACTIVATED = "DEACTIVATED"  # Деактивирована
    SUSPENDED = "SUSPENDED" # Приостановлена
    ERROR = "ERROR"         # Ошибка

    def is_active(self) -> bool:
        return self in (ServiceStatus.ACTIVE, ServiceStatus.PROGRESS)

    def is_terminal(self) -> bool:
        return self in (ServiceStatus.DEACTIVATED, ServiceStatus.ERROR)
