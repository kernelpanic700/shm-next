# =============================================================================
# shm-next — Unit Tests: Config
# =============================================================================
"""Тесты конфигурации."""

from __future__ import annotations

from app.api.config import AppConfig, get_app_config


class TestAppConfig:
    """Тесты AppConfig."""

    def test_default_values(self):
        config = AppConfig()
        assert config.app_name == "shm-next"
        assert config.debug is False
        assert config.api_host == "0.0.0.0"
        assert config.api_port == 8000
        assert config.database_url.startswith("postgresql+asyncpg")

    def test_test_config(self):
        from app.api.config import TestConfig
        config = TestConfig()
        assert config.debug is True
        assert config.database_url.endswith("shm_test")
        assert config.log_level == "DEBUG"

    def test_secret_key_not_empty(self):
        config = AppConfig()
        assert len(config.secret_key) > 10

    def test_get_app_config_cached(self):
        config1 = get_app_config()
        config2 = get_app_config()
        assert config1 is config2

    def test_jwt_settings(self):
        config = AppConfig()
        assert config.algorithm == "HS256"
        assert config.access_token_expire_minutes > 0
        assert config.refresh_token_expire_days > 0

    def test_cors_origins(self):
        config = AppConfig()
        assert isinstance(config.cors_origins, list)
        assert len(config.cors_origins) > 0
