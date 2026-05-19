# =============================================================================
# shm-next — Period Value Object
# =============================================================================
from __future__ import annotations

from datetime import date


class Period:
    """
    Период для биллинговых расчётов.

    Attributes:
        start: Начало периода (включительно)
        end: Конец периода (включительно)
    """

    def __init__(self, start: date, end: date) -> None:
        if start > end:
            raise ValueError(f"Period start ({start}) cannot be after end ({end})")
        self._start = start
        self._end = end

    @property
    def start(self) -> date:
        return self._start

    @property
    def end(self) -> date:
        return self._end

    @property
    def days(self) -> int:
        return (self._end - self._start).days + 1

    def contains(self, d: date) -> bool:
        """Проверяет, содержит ли период указанную дату."""
        return self._start <= d <= self._end

    def overlaps(self, other: Period) -> bool:
        """Проверяет пересечение с другим периодом."""
        return self._start <= other._end and other._start <= self._end

    @classmethod
    def month(cls, year: int, month: int) -> Period:
        """Создать период для указанного месяца."""
        import calendar
        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])
        return cls(start, end)

    @classmethod
    def from_string(cls, period_str: str) -> Period:
        """Парсинг периода из строки формата 'YYYY-MM:YYYY-MM'."""
        parts = period_str.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid period format: {period_str}")
        start = date.fromisoformat(parts[0] + "-01")
        end = date.fromisoformat(parts[1] + "-01")
        import calendar
        end = end.replace(day=calendar.monthrange(end.year, end.month)[1])
        return cls(start, end)

    def __repr__(self) -> str:
        return f"Period({self._start}, {self._end})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return self._start == other._start and self._end == other._end

    def __hash__(self) -> int:
        return hash((self._start, self._end))
