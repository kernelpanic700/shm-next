# =============================================================================
# shm-next — Tracing Middleware
# =============================================================================
"""
Настройка OpenTelemetry трейсинга.

Каждый HTTP-запрос автоматически получает trace span.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.litestar import LitestarInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.api.config import AppConfig


def setup_tracing(config: AppConfig) -> None:
    """
    Инициализация OpenTelemetry трейсинга.

    Если OTLP-экспортёр не настроен, трейсинг отключается.
    """
    if not config.otel_exporter_otlp_endpoint:
        return

    resource = Resource.create(
        {
            "service.name": config.otel_service_name,
            "service.version": "3.0.0",
        }
    )

    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=config.otel_exporter_otlp_endpoint,
        insecure=True,
    )

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def setup_litestar_tracing(app):
    """Автоматическая инструментация Litestar."""
    LitestarInstrumentor().instrument_app(app)
