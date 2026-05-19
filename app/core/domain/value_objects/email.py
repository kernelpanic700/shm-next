# =============================================================================
# shm-next — Email Value Object
# =============================================================================
"""
Value Object для email-адреса.

Обеспечивает базовую валидацию формата email.
"""

from __future__ import annotations

import re
from typing import Any


class Email:
    """
    Email-адрес.

    Валидация по RFC-подобному паттерну.
    Не гарантирует 100% соответствие RFC 5322,
    но покрывает >99% реальных email-адресов.
    """

    _PATTERN = re.compile(
        r"^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+"
        r"@"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
    )

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        value = value.strip().lower()
        if not self._PATTERN.match(value):
            raise ValueError(f"Невалидный email: '{value}'")
        self._value = value

    @property
    def value(self) -> str:
        return self._value

    @property
    def local_part(self) -> str:
        return self._value.split("@")[0]

    @property
    def domain(self) -> str:
        return self._value.split("@")[1]

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"Email('{self._value}')"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Email):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)
