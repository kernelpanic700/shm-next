# =============================================================================
# shm-next — Observability: Tracing
# =============================================================================
"""
OpenTelemetry трейсинг для распределённой диагностики.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory import InMemorySpanExporter

_tracer_provider: TracerProvider | None = None


def get_tracer() -> trace.Tracer:
    """Получить трейсер для текущего модуля."""
    return trace.get_tracer("shm-next")


def get_in_memory_exporter() -> InMemorySpanExporter:
    """
    Получить InMemorySpanExporter для тестов.

    Используется в тестах для проверки создания спанов.
    """
    exporter = InMemorySpanExporter()
    return exporter
