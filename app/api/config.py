# =============================================================================
# shm-next — Application Configuration
# =============================================================================
"""
Конфигурация приложения.

Использует pydantic-settings для загрузки из переменных окружения.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseSettingsConfig(BaseSettings):
    """Базовая конфигурация загрузки из .env."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class AppConfig(BaseSettingsConfig):
    """
    Основная конфигурация приложения.

    Все значения читаются из переменных окружения с дефолтами.
    """

    # === Приложение ===
    app_name: str = "shm-next"
    debug: bool = Field(default=False)
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    workers: int = Field(default=4)
    reload: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # === Безопасность ===
    secret_key: str = Field(default="dev-secret-key-change-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )
    allowed_hosts: list[str] = Field(default=["*"])

    # === База данных ===
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/shm"
    )
    db_pool_size: int = Field(default=10)
    db_max_overflow: int = Field(default=20)
    db_echo: bool = Field(default=False)

    # === Redis ===
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_cache_ttl: int = Field(default=300)

    # === Taskiq ===
    taskiq_broker_url: str = Field(default="redis://localhost:6379/1")
    taskiq_result_backend: str = Field(default="redis://localhost:6379/2")
    taskiq_max_retries: int = Field(default=3)
    taskiq_retry_delay: int = Field(default=5)
    billing_batch_size: int = Field(default=100)

    # === Email ===
    smtp_host: str = Field(default="")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    smtp_use_tls: bool = Field(default=True)
    email_from: str = Field(default="noreply@shm.local")
    email_templates_dir: str = Field(default="templates/email")

    # === SMS ===
    sms_api_url: str = Field(default="")
    sms_api_key: str = Field(default="")
    sms_sender: str = Field(default="SHM")

    # === OpenTelemetry ===
    otel_endpoint: str = Field(default="")
    otel_service_name: str = Field(default="shm-next")
    otel_exporter_otlp_endpoint: str = Field(default="")

    # === Rate Limiting ===
    rate_limit_default: str = Field(default="100/minute")
    rate_limit_auth: str = Field(default="5/minute")
    rate_limit_api: str = Field(default="200/minute")

    # === Биллинг ===
    billing_cycle_day: int = Field(default=1)
    default_currency: str = Field(default="RUB")

    # === Sentry ===
    sentry_dsn: str = Field(default="")


class TestConfig(AppConfig):
    """Конфигурация для тестов."""

    debug: bool = Field(default=True)
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/shm_test"
    )
    log_level: str = Field(default="DEBUG")
    smtp_host: str = Field(default="")
    sms_api_url: str = Field(default="")
    otel_endpoint: str = Field(default="")


# Глобальный кэш конфигурации
_config_cache: AppConfig | None = None


def get_app_config() -> AppConfig:
    """
    Получить конфигурацию приложения (синглтон).

    Returns:
        AppConfig: Экземпляр конфигурации
    """
    global _config_cache
    if _config_cache is None:
        _config_cache = AppConfig()
    return _config_cache


def reset_config_cache() -> None:
    """Сбросить кэш конфигурации (для тестов)."""
    global _config_cache
    _config_cache = None
