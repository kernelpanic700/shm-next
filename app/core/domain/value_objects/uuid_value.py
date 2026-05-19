# =============================================================================
# shm-next — UUID Value Object
# =============================================================================
"""
Обёртка над uuid.UUID с валидацией.

Используется как value object для гарантии корректности UUID-значений
на уровне доменного слоя.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4


class UUIDValue:
    """
    Value Object для UUID.

    Гарантирует, что значение является валидным UUID.
    Неизменяем после создания.
    """

    __slots__ = ("_value",)

    def __init__(self, value: UUID | str | None = None) -> None:
        if value is None:
            self._value = uuid4()
        elif isinstance(value, UUID):
            self._value = value
        elif isinstance(value, str):
            self._value = UUID(value)
        else:
            raise TypeError(
                f"Ожидался UUID или str, получен {type(value).__name__}"
            )

    @classmethod
    def generate(cls) -> UUIDValue:
        return cls(uuid4())

    @property
    def value(self) -> UUID:
        return self._value

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"UUIDValue('{self._value}')"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, UUIDValue):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)
