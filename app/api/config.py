# =============================================================================
# shm-next — Application Configuration
# =============================================================================
"""
Конфигурация приложения.

Использует pydantic-settings для загрузки из переменных окружения.
"""

from typing import Any, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseSettingsConfig(BaseSettings):
    """Базовая конфигурация загрузки из .env."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        enable_decoding=False,
    )


def parse_cors_origins(v: Union[str, list[str]]) -> list[str]:
    """Parse CORS origins from string or list."""
    if isinstance(v, str):
        return [item.strip() for item in v.split(",") if item.strip()]
    return v or []


def parse_allowed_hosts(v: Union[str, list[str]]) -> list[str]:
    """Parse allowed hosts from string or list."""
    if isinstance(v, str):
        return [item.strip() for item in v.split(",") if item.strip()]
    return v or []


def parse_bool_flag(v: Any) -> bool:
    """Parse boolean-like environment values used by legacy deploy configs."""
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        normalized = v.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on", "debug", "dev", "development"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", "release", "prod", "production"}:
            return False
    return bool(v)


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
    admin_phone: str = Field(default="")
    admin_password: str = Field(default="")
    admin_password_hash: str = Field(default="")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:8080"],
    )
    allowed_hosts: list[str] = Field(default=["*"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, v: Union[str, list[str], None]) -> list[str]:
        return parse_cors_origins(v)

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def validate_allowed_hosts(cls, v: Union[str, list[str], None]) -> list[str]:
        return parse_allowed_hosts(v)

    @field_validator("debug", "reload", "db_echo", "smtp_use_tls", mode="before")
    @classmethod
    def validate_bool_flags(cls, v: Any) -> bool:
        return parse_bool_flag(v)

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
