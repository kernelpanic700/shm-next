# =============================================================================
# shm-next — Currency Value Object
# =============================================================================
from __future__ import annotations

from enum import Enum


class Currency(Enum):
    """Поддерживаемые валюты."""
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"
    UZS = "UZS"

    @property
    def decimal_places(self) -> int:
        """Количество знаков после запятой."""
        mapping = {
            "RUB": 2,
            "USD": 2,
            "EUR": 2,
            "KZT": 2,
            "UZS": 2,
        }
        return mapping.get(self.value, 2)
