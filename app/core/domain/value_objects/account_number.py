# =============================================================================
# shm-next — AccountNumber Value Object
# =============================================================================
"""
Value Object для номера лицевого счёта.

Номер лицевого счёта — уникальный идентификатор абонента
в биллинговой системе.
"""

from __future__ import annotations

from typing import Any


class AccountNumber:
    """
    Номер лицевого счёта абонента.

    Инварианты:
    - Не пустая строка
    - Длина от 1 до 20 символов
    - Только алфавитно-цифровые символы и дефисы
    """

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        if not value or not isinstance(value, str):
            raise ValueError("Номер лицевого счёта не может быть пустым")
        cleaned = value.strip()
        if len(cleaned) > 20:
            raise ValueError(
                f"Номер лицевого счёта слишком длинный: "
                f"{len(cleaned)} символов (макс. 20)"
            )
        if not cleaned.replace("-", "").isalnum():
            raise ValueError(
                f"Номер лицевого счёта содержит недопустимые символы: '{value}'. "
                f"Разрешены: буквы, цифры, дефис"
            )
        self._value = cleaned

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"AccountNumber('{self._value}')"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, AccountNumber):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)
