# shm-next — Universal Billing System

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Современная система биллинга на Python с архитектурой Clean Architecture.

## 📋 Содержание

- [Быстрый старт](#-быстрый-старт)
- [Архитектура](#-архитектура)
- [Установка](#-установка)
- [Конфигурация](#-конфигурация)
- [Запуск](#-запуск)
- [API](#-api)
- [Разработка](#-разработка)
- [Тестирование](#-тестирование)
- [Деплой](#-деплой)

## 🚀 Быстрый старт

```bash
# 1. Клонирование и настройка
git clone <repo-url>
cd shm-next

# 2. Установка зависимостей
pip install -e ".[dev]"

# 3. Настройка окружения
cp .env.example .env
# Отредактировать .env под свои нужды

# 4. Запуск тестов
pytest tests/ -v

# 5. Запуск API сервера
uvicorn app.api.app:app --reload
```

## 🏗️ Архитектура

```
shm-next/
├── app/                    # Основной код
│   ├── api/               # API слой (Litestar)
│   ├── core/              # Доменный слой
│   ├── infrastructure/    # Инфраструктурный слой
│   └── worker/            # Фоновые задачи (Taskiq)
├── tests/                 # Тесты
├── alembic/               # Миграции БД
└── docker-compose.yml       # Docker оркестрация
```

### Слои архитектуры

- **API Layer** — REST API на Litestar
- **Core Layer** — Доменные сущности и бизнес-логика
- **Infrastructure Layer** — Репозитории, БД, внешние сервисы
- **Worker Layer** — Асинхронные задачи через Taskiq

## 📦 Установка

### Требования

- Python 3.12+
- PostgreSQL 14+
- Redis 7+

### Локальная установка

```bash
# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate

# Установка зависимостей
pip install -e ".[dev]"
```

### Docker установка

```bash
# Запуск всех сервисов
docker compose --profile dev up -d

# Остановка
docker compose down
```

## ⚙️ Конфигурация

Основные переменные окружения (см. `.env.example`):

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `DATABASE_URL` | Строка подключения к PostgreSQL | `postgresql://...` |
| `REDIS_URL` | URL Redis | `redis://localhost:6379/0` |
| `SECRET_KEY` | Секретный ключ для JWT | обязательно изменить |
| `DEBUG` | Режим отладки | `false` |

## ▶️ Запуск

### API сервер

```bash
# Разработка (с hot-reload)
uvicorn app.api.app:app --reload --port 8000

# Продакшен
uvicorn app.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Worker

```bash
# Запуск воркера
taskiq app.worker.app:broker --workers 2
```

### Docker

```bash
# Development
docker compose --profile dev up -d

# Production
docker compose --profile prod up -d
```

## 📡 API

### Эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/health` | Проверка здоровья |
| POST | `/api/v1/auth/login` | Авторизация |
| POST | `/api/v1/auth/refresh` | Обновление токена |
| GET | `/api/v1/abonents` | Список абонентов |
| POST | `/api/v1/abonents` | Создание абонента |
| GET | `/api/v1/abonents/{id}` | Получить абонента |
| PUT | `/api/v1/abonents/{id}` | Обновить абонента |
| DELETE | `/api/v1/abonents/{id}` | Удалить абонента |
| GET | `/api/v1/tariffs` | Список тарифов |
| POST | `/api/v1/tariffs` | Создать тариф |
| GET | `/api/v1/invoices` | Список счетов |
| POST | `/api/v1/invoices` | Создать счет |
| POST | `/api/v1/payments` | Создать платеж |

### Примеры ключевых API-запросов

```bash
# Health check
curl http://localhost:8000/api/v1/health
# {"status":"healthy","timestamp":"2026-05-19T10:00:00Z"}

# Авторизация
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"secret"}'
# {"access_token":"...","refresh_token":"...","token_type":"bearer"}

# Создание абонента
curl -X POST http://localhost:8000/api/v1/abonents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","full_name":"Иван Иванов"}'

# Получение списка абонентов с пагинацией
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/abonents?page=1&size=20"

# Создание тарифа
curl -X POST http://localhost:8000/api/v1/tariffs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Базовый","price":500,"currency":"RUB"}'

# Создание платежа
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"abonent_id":"...","amount":1000,"method":"card"}'
```

## 🛠️ Разработка

### Структура проекта

```bash
# Запуск линтера
ruff check app tests
ruff format app tests

# Типы
mypy app

# Тесты
pytest tests/ -v --cov=app
```

### Добавление нового сервиса

1. Создать сущность в `app/core/domain/entities/`
2. Создать репозиторий в `app/core/domain/repositories/`
3. Реализовать репозиторий в `app/infrastructure/db/repositories/`
4. Добавить сервис в `app/core/services/`
5. Добавить контроллер в `app/api/v1/`

## 🎨 Admin Panel

Современный веб-интерфейс на Next.js 14 (App Router) для управления системой.

### Страницы

| Страница | Описание |
|----------|----------|
| `/abonents` | Управление абонентами (поиск, фильтры, действия) |
| `/abonents/[id]` | Детальная карточка абонента с историей |
| `/tariffs` | Список тарифов |
| `/services` | Управление услугами |
| `/payments` | Мониторинг платежей |
| `/spool` | Очередь задач (SPOOL) |
| `/reports` | Аналитика и отчёты |

### Запуск Admin Panel

```bash
cd admin
npm install
npm run dev      # http://localhost:3000
npm run build    # Production сборка
```

### Технологии

- **Next.js 14.2** + App Router
- **TypeScript** + TanStack Query v5
- **TanStack Table v8** + Radix UI
- **Recharts** для графиков
- **Tailwind CSS**

## 🧪 Тестирование

```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest tests/ --cov=app --cov-report=html

# Конкретный файл
pytest tests/integration/test_abonent_repo.py -v
```

## 🚢 Деплой

### Docker Compose (рекомендуется)

```bash
# Скопировать .env.example как .env и настроить
cp .env.example .env

# Запустить продакшен
docker compose --profile prod up -d
```

### Ручной деплой

```bash
# 1. Миграции БД
alembic upgrade head

# 2. Запуск API
gunicorn app.api.app:app -w 4 -k uvicorn.workers.UvicornWorker

# 3. Запуск воркера
taskiq app.worker.app:broker --workers 4
```

## 📊 Мониторинг

- **Health**: `GET /api/v1/health`
- **Metrics**: Prometheus endpoint (при включении)
- **Logs**: JSON формат в продакшене

## 🗺️ Roadmap

### v0.2.0 (Ближайшие 2 недели)
- [ ] Admin Panel на React/Next.js
- [ ] Rate limiting middleware
- [ ] Request/response logging

### v0.3.0 (Месяц)
- [ ] Security hardening (OWASP)
- [ ] Performance optimization (caching, query optimization)
- [ ] OpenTelemetry tracing

### v1.0.0 (Долгосрочно)
- [ ] Multi-tenancy support
- [ ] Advanced reporting
- [ ] Webhook system
- [ ] GraphQL API

## 🤝 Contributing

1. Fork репозитория
2. Создать feature ветку (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push ветку (`git push origin feature/amazing-feature`)
5. Открыть Pull Request

## 📄 Лицензия

MIT License — см. [LICENSE](LICENSE) файл.