# =============================================================================
# shm-next — Base Value Object
# =============================================================================
"""
Базовый класс для Value Objects.

Value Objects — неизменяемые объекты, определяемые своими атрибутами.
Не имеют идентичности (не сравниваются по ID).
"""

from __future__ import annotations

from typing import Any


class ValueObject:
    """
    Базовый класс Value Object.

    Value Objects:
    - Неизменяемы (immutable) после создания
    - Сравниваются по значению, а не по идентичности
    - Могут валидировать свои инварианты при создании
    """

    def __eq__(self, other: Any) -> bool:
        if other is None or not isinstance(other, self.__class__):
            return NotImplemented
        return self._attrs() == other._attrs()

    def __hash__(self) -> int:
        return hash(self._attrs())

    def _attrs(self) -> tuple:
        """Кортеж атрибутов для сравнения и хэширования."""
        raise NotImplementedError

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_"))
        return f"{self.__class__.__name__}({attrs})"
