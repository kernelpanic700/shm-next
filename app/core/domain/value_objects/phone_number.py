# =============================================================================
# shm-next — PhoneNumber Value Object
# =============================================================================
"""
Value Object для номера телефона.

Обеспечивает валидацию формата и неизменяемость.
"""

from __future__ import annotations

import re
from typing import Any


class PhoneNumber:
    """
    Номер телефона.

    Валидирует формат при создании.
    Поддерживает российские и международные форматы.
    """

    _PATTERN = re.compile(
        r"^"
        r"(\+?7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})"
        r"|(\+?\d{1,3}[\s\-]?\(?\d{1,5}\)?[\s\-]?\d{1,14})"
        r"$"
    )

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        cleaned = self._clean(value)
        if not self._PATTERN.match(cleaned):
            raise ValueError(
                f"Невалидный номер телефона: '{value}'. "
                f"Ожидается формат: +7XXXXXXXXXX или 8XXXXXXXXXX"
            )
        self._value = cleaned

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"[\s\-\(\)]", "", value)

    @property
    def value(self) -> str:
        return self._value

    @property
    def digits_only(self) -> str:
        return re.sub(r"\D", "", self._value)

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"PhoneNumber('{self._value}')"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PhoneNumber):
            return NotImplemented
        return self.digits_only == other.digits_only

    def __hash__(self) -> int:
        return hash(self.digits_only)
