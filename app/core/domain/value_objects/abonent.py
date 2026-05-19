# =============================================================================
# shm-next — Abonent Status
# =============================================================================
from __future__ import annotations

from enum import Enum


class AbonentStatus(Enum):
    """Статусы абонента."""
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    DISABLED = "DISABLED"
    DELETED = "DELETED"
    INACTIVE = "INACTIVE"

    def is_active(self) -> bool:
        return self == AbonentStatus.ACTIVE
