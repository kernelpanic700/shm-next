# Changelog

Все значимые изменения в этом проекте будут документированы в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
а версии - на [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.0] - 2026-05-21

### Добавлено ✨

#### Backend (API)
- REST API на Litestar с полной поддержкой CRUD для абонентов, тарифов, услуг
- JWT-аутентификация с refresh-токенами
- Taskiq worker для асинхронных задач (SPOOL)
- Alembic миграции для PostgreSQL
- Redis кэширование и rate limiting
- Полноценный health endpoint `/api/v1/health`
- OpenAPI/Swagger документация

#### Frontend (Admin Panel)
- Современный UI на Next.js 14.2 (App Router)
- Страница абонентов с поиском, фильтрами, пагинацией
- Детальная страница абонента с табами (инфо, услуги, платежи, история)
- Управление тарифами и услугами
- Мониторинг платежей с фильтрацией по статусу
- SPOOL: мониторинг очереди задач с retry/cancel
- Аналитика: метрики, графики (LineChart, PieChart, BarChart), экспорт CSV
- Responsive дизайн на Tailwind CSS

#### Инфраструктура
- Docker Compose для dev/prod окружений
- PostgreSQL 16 + Redis 7
- Prometheus метрики
- OpenTelemetry трассировка

### Технологический стек

**Backend:**
- Python 3.12 + Litestar 2.8
- SQLAlchemy 2.0 (async)
- PostgreSQL 16
- Redis 7 + Taskiq
- Alembic

**Frontend:**
- Next.js 14.2 + TypeScript
- TanStack Query v5 + TanStack Table v8
- Radix UI + Tailwind CSS
- Recharts

### Тестирование
- 455 тестов с 50%+ покрытием
- pytest + pytest-asyncio + factory-boy

---

## План v0.2.0

### Безопасность
- Rate limiting на уровне API
- CSP заголовки и security headers
- Аудит действий администраторов

### Производительность
- Redis кэширование часто используемых запросов
- Оптимизация slow queries
- Connection pooling

### Функционал
- Расширенные отчёты (по дням, тарифам, абонентам)
- Mobile-адаптация Admin Panel
- Push-уведомления

### DevOps
- CI/CD pipeline (GitHub Actions)
- Автоматический деплой
- Миграция на Kubernetes