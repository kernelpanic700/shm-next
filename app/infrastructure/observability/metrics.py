# =============================================================================
# shm-next — Observability: Metrics
# =============================================================================
"""
Prometheus метрики для мониторинга приложения.

Используется prometheus-client для экспорта метрик.
"""

from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
)


class MetricsCollector:
    """
    Коллектор бизнес-метрик приложения.

    Метрики:
    - HTTP запросы (Counter, Histogram)
    - Биллинг операции (Counter)
    - Очередь задач (Gauge)
    - Балансы (Summary)
    - Ошибки (Counter)
    """

    # === HTTP Метрики ===
    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status_code"],
    )
    http_request_duration = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration",
        ["method", "path"],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )

    # === Биллинг ===
    billing_cycles_total = Counter(
        "billing_cycles_total",
        "Total billing cycles completed",
        ["status"],
    )
    billing_withdraws_total = Counter(
        "billing_withdraws_total",
        "Total withdrawal operations",
        ["status", "service_type"],
    )
    billing_balance = Gauge(
        "billing_balance_total",
        "Total balance across all abonents",
        ["currency"],
    )

    # === Задачи ===
    queue_tasks_total = Counter(
        "queue_tasks_total",
        "Total tasks processed",
        ["queue", "status"],
    )
    queue_tasks_pending = Gauge(
        "queue_tasks_pending",
        "Number of pending tasks",
        ["queue"],
    )

    # === Платежи ===
    payments_total = Counter(
        "payments_total",
        "Total payment operations",
        ["status", "method"],
    )
    payments_amount = Summary(
        "payments_amount_total",
        "Total payment amounts",
        ["currency"],
    )

    # === Ошибки ===
    errors_total = Counter(
        "errors_total",
        "Total errors",
        ["type", "module"],
    )

    # === Сессии ===
    active_sessions = Gauge(
        "active_sessions",
        "Number of active sessions",
    )

    # === Абоненты ===
    abonents_total = Gauge(
        "abonents_total",
        "Total abonents",
        ["status"],
    )

    @classmethod
    def get_metrics_response(cls) -> tuple[bytes, str]:
        """
        Возвращает метрики в формате Prometheus.

        Returns:
            tuple: (metrics_bytes, content_type)
        """
        return generate_latest(), CONTENT_TYPE_LATEST


def setup_metrics() -> None:
    """Инициализация метрик (предварительная настройка)."""
    pass
