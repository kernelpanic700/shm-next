# =============================================================================
# shm-next — Multi-stage Dockerfile
# =============================================================================
# Stage 1: Builder — установка зависимостей и компиляция
# Stage 2: Runtime — минимальный образ для продакшена
# =============================================================================

# ============================================================
# Stage 1: Builder
# ============================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Устанавливаем системные зависимости для компиляции
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv (быстрая альтернатива pip)
RUN pip install --no-cache-dir uv>=0.4.0

# Копируем файлы зависимостей
COPY pyproject.toml ./

# Создаём виртуальное окружение и устанавливаем зависимости
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install .

# ============================================================
# Stage 2: Runtime
# ============================================================
FROM python:3.12-slim AS runtime

# Метаданные
LABEL maintainer="shm-team"
LABEL description="SHM Next — Universal Billing System"

# Создаём non-root пользователя
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Устанавливаем минимальные системные зависимости (только runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app"

# Создаём рабочую директорию
WORKDIR /app

# Копируем исходный код
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY worker/ ./worker/

# Владелец — non-root пользователь
RUN chown -R appuser:appuser /app

USER appuser

# Healthcheck для API сервера
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Порты
EXPOSE 8000

# Точка входа
CMD ["uvicorn", "app.api.app:app", "--host", "0.0.0.0", "--port", "8000"]