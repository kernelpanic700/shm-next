# =============================================================================
# shm-next — Makefile
# =============================================================================
# Основные команды для разработки и эксплуатации
#
# Использование:
#   make dev          — запуск dev-среды (docker compose)
#   make test         — запуск тестов
#   make lint         — проверка кода (ruff + mypy)
#   make format       — автоформатирование кода
#   make migrate      — создание и применение миграций
#   make build        — сборка Docker-образов
#   make up           — запуск продакшн-окружения
#   make down         — остановка окружения
# =============================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

# === Переменные ===
PYTHON ?= python3
UV ?= uv
DOCKER_COMPOSE := docker compose
APP_DIR := app
TEST_DIR := tests

# === Цвета ===
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

# =============================================================================
# Разработка
# =============================================================================

.PHONY: dev
dev: ## Запуск dev-среды (docker compose с hot-reload)
	@echo "$(GREEN)🚀 Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) --profile dev up --build

.PHONY: dev-down
dev-down: ## Остановка dev-среды
	@echo "$(YELLOW)🛑 Stopping development environment...$(NC)"
	$(DOCKER_COMPOSE) --profile dev down

.PHONY: dev-migrate
dev-migrate: ## Применение миграций в dev
	@echo "$(GREEN)🔄 Running migrations in dev...$(NC)"
	$(DOCKER_COMPOSE) --profile dev exec api alembic upgrade head

.PHONY: logs
logs: ## Просмотр логов
	$(DOCKER_COMPOSE) --profile dev logs -f --tail=100

.PHONY: logs-api
logs-api: ## Просмотр логов API
	$(DOCKER_COMPOSE) --profile dev logs -f --tail=100 api

.PHONY: logs-worker
logs-worker: ## Просмотр логов Worker
	$(DOCKER_COMPOSE) --profile dev logs -f --tail=100 worker

# =============================================================================
# Тестирование
# =============================================================================

.PHONY: test
test: ## Запуск всех тестов
	@echo "$(GREEN)🧪 Running tests...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR) --cov=$(APP_DIR) --cov-report=term-missing

.PHONY: test-unit
test-unit: ## Запуск unit-тестов
	@echo "$(GREEN)🧪 Running unit tests...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR)/unit -v

.PHONY: test-integration
test-integration: ## Запуск интеграционных тестов
	@echo "$(GREEN)🧪 Running integration tests...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR)/integration -v

.PHONY: test-slow
test-slow: ## Запуск медленных тестов
	@echo "$(GREEN)🧪 Running slow tests...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR) -m slow -v

.PHONY: test-cov
test-cov: ## Тесты с генерацией отчёта покрытия
	@echo "$(GREEN)🧪 Running tests with coverage...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR) --cov=$(APP_DIR) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report: htmlcov/index.html$(NC)"

.PHONY: test-cov-min
test-cov-min: ## Проверка покрытия (с порогом)
	@echo "$(GREEN)🧪 Checking coverage threshold...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR) --cov=$(APP_DIR) --cov-fail-under=80

# =============================================================================
# Линтинг и форматирование
# =============================================================================

.PHONY: lint
lint: ## Проверка кода (ruff + mypy)
	@echo "$(YELLOW)🔍 Linting code...$(NC)"
	@echo "  → Ruff..."
	ruff check $(APP_DIR) $(TEST_DIR)
	@echo "  → Mypy..."
	mypy $(APP_DIR) $(TEST_DIR)
	@echo "$(GREEN)✅ Lint passed$(NC)"

.PHONY: lint-fix
lint-fix: ## Автоисправление линтинга
	@echo "$(YELLOW)🔧 Fixing lint issues...$(NC)"
	ruff check --fix $(APP_DIR) $(TEST_DIR)

.PHONY: format
format: ## Автоформатирование кода
	@echo "$(YELLOW)✨ Formatting code...$(NC)"
	ruff format $(APP_DIR) $(TEST_DIR)
	isort $(APP_DIR) $(TEST_DIR)
	@echo "$(GREEN)✅ Formatting done$(NC)"

.PHONY: typecheck
typecheck: ## Проверка типов (mypy)
	@echo "$(YELLOW)🔍 Type checking...$(NC)"
	mypy $(APP_DIR) $(TEST_DIR)
	@echo "$(GREEN)✅ Type check passed$(NC)"

# =============================================================================
# Миграции базы данных
# =============================================================================

.PHONY: migrate-init
migrate-init: ## Инициализация Alembic (один раз)
	@echo "$(GREEN)🔄 Initializing Alembic...$(NC)"
	alembic init alembic

.PHONY: migrate-revision
migrate-revision: ## Создание новой миграции (автогенерация)
	@echo "$(GREEN)📝 Creating migration...$(NC)"
	alembic revision --autogenerate -m "$(MSG)"

.PHONY: migrate-revision-empty
migrate-revision-empty: ## Создание пустой миграции
	@echo "$(GREEN)📝 Creating empty migration...$(NC)"
	alembic revision -m "$(MSG)"

.PHONY: migrate-upgrade
migrate-upgrade: ## Применение всех миграций
	@echo "$(GREEN)🔄 Upgrading database...$(NC)"
	alembic upgrade head

.PHONY: migrate-downgrade
migrate-downgrade: ## Откат последней миграции
	@echo "$(YELLOW)⬇️ Downgrading database...$(NC)"
	alembic downgrade -1

.PHONY: migrate-history
migrate-history: ## История миграций
	alembic history --verbose

.PHONY: migrate-current
migrate-current: ## Текущая версия БД
	alembic current

.PHONY: migrate-stamp
migrate-stamp: ## Отметить БД как текущую (без выполнения)
	alembic stamp head

# =============================================================================
# Сборка и деплой
# =============================================================================

.PHONY: build
build: ## Сборка Docker-образов
	@echo "$(GREEN)🏗️ Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) --profile prod build

.PHONY: build-no-cache
build-no-cache: ## Сборка без кэша
	@echo "$(GREEN)🏗️ Building Docker images (no cache)...$(NC)"
	$(DOCKER_COMPOSE) --profile prod build --no-cache

.PHONY: up
up: ## Запуск продакшн-окружения
	@echo "$(GREEN)🚀 Starting production environment...$(NC)"
	$(DOCKER_COMPOSE) --profile prod up -d --build

.PHONY: down
down: ## Остановка окружения
	@echo "$(YELLOW)🛑 Stopping environment...$(NC)"
	$(DOCKER_COMPOSE) down

.PHONY: down-v
down-v: ## Остановка с удалением volumes
	@echo "$(RED)💀 Stopping and removing volumes...$(NC)"
	$(DOCKER_COMPOSE) down -v

# =============================================================================
# Утилиты
# =============================================================================

.PHONY: shell
shell: ## Запуск shell в контейнере API
	$(DOCKER_COMPOSE) --profile dev exec api /bin/sh

.PHONY: shell-db
shell-db: ## Запуск psql в контейнере БД
	$(DOCKER_COMPOSE) --profile dev exec postgres psql -U $(DB_USER:-shm) -d $(DB_NAME:-shm)

.PHONY: seed
seed: ## Заполнение тестовыми данными
	@echo "$(GREEN)🌱 Seeding database...$(NC)"
	$(PYTHON) scripts/seed.py

.PHONY: clean
clean: ## Очистка кешей и артефактов
	@echo "$(YELLOW)🧹 Cleaning...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml 2>/dev/null || true

.PHONY: help
help: ## Показать эту справку
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'