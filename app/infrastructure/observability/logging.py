# =============================================================================
# shm-next — Logging Configuration
# =============================================================================
"""
Настройка логирования.

Используется structlog для структурированного логирования.
Поддерживает JSON-формат для продакшена и человекочитаемый для разработки.
"""

from __future__ import annotations

import logging
import sys

import structlog

from app.api.config import AppConfig


def setup_logging() -> None:
    """
    Настройка логирования приложения.

    Читает конфигурацию и настраивает structlog.
    """
    config = AppConfig()

    # Shared processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    # Renderer в зависимости от формата
    if config.log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    # Конфигурация structlog
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Настройка стандартного logging
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(config.log_level.upper())

    # Уменьшаем шум от сторонних библиотек
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    logging.getLogger("taskiq").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """Получить логгер для модуля."""
    return structlog.get_logger(name)


def setup_tracing(service_name: str = "shm-next") -> None:
    """Настроить OpenTelemetry tracing."""
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ModuleNotFoundError:
        logging.getLogger(__name__).warning(
            "OpenTelemetry exporter is not installed; tracing disabled"
        )
        return

    resource = Resource.create({"service.name": service_name})

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
