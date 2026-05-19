# =============================================================================
# shm-next — Application Entry Point
# =============================================================================
"""
Точка входа приложения Litestar.

Использование:
    uvicorn app.api.app:app --reload --port 8000
    # или
    python -m app.api.main
"""

from __future__ import annotations

from litestar import Litestar

from app.api.app import create_application
from app.api.config import AppConfig, get_app_config


def get_application() -> Litestar:
    """
    Создание и конфигурация приложения Litestar.

    Returns:
        Litestar: Сконфигурированное приложение
    """
    return create_application()


def main() -> None:
    """Entry point для запуска через `python -m app.api.main` или `uvicorn`."""
    import uvicorn

    config: AppConfig = get_app_config()

    uvicorn.run(
        "app.api.app:app",
        host=config.api_host,
        port=config.api_port,
        factory=False,
        reload=config.debug,
        log_level=config.log_level.lower(),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
