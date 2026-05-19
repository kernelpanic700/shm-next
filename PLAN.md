## План реализации по этапам

### Этап 0: Подготовка (1–2 недели)
- [x] Создать репозиторий `shm-python`
- [x] Настроить структуру проекта (`pyproject.toml`, `Makefile`, `pre-commit`)
- [x] Настроить CI/CD (GitHub Actions)
- [x] Развернуть тестовое окружение (Docker Compose)
- [x] Написать Alembic миграции на основе существующей схемы

### Этап 1: Domain Layer (2–3 недели)
- [ ] Создать все domain entities (User, Service, UserService, Withdraw, Payment, SpoolTask, Event, Config, Discount, Invoice, BonusEntry, Session)
- [ ] Определить value objects (Money, Period, Status, EventType)
- [ ] Определить abstract repository interfaces
- [ ] Написать unit-тесты для domain entities

### Этап 2: Infrastructure — DB (2–3 недели)
- [ ] Настроить SQLAlchemy 2.0 + asyncpg
- [ ] Написать все ORM-модели
- [ ] Реализовать concrete repositories
- [ ] Написать Alembic миграции
- [ ] Настроить Redis-кэш
- [ ] Integration-тесты для DB layer

### Этап 3: Core Billing Engine (2–3 недели)
- [ ] Реализовать `BillingEngine` (calc_withdraw, calc_payment, calc_available_bonuses)
- [ ] Реализовать обе стратегии: Honest и Simpler
- [ ] Реализовать `create_service`, `prolongate_service`, `money_back`, `switch_tariff`
- [ ] Unit-тесты для всех расчётов (100% coverage)
- [ ] Property-based тесты (hypothesis)

### Этап 4: External Actions / Spool System (3–4 недели)
- [ ] Реализовать `SpoolTask` entity + repository
- [ ] Реализовать `ExternalActionRegistry`
- [ ] Реализовать `PluginManager` + `PluginSandbox`
- [ ] Реализовать Celery worker для обработки задач
- [ ] Retry logic, DLQ, exponential backoff
- [ ] Webhook client для внешних HTTP-вызовов
- [ ] Integration-тесты

### Этап 5: Auth & Users (2–3 недели)
- [ ] Регистрация, авторизация, JWT, OTP
- [ ] Сессии (Redis + DB)
- [ ] Rate limiting
- [ ] Password reset, email verification
- [ ] Баланс, бонусы, кредит (атомарные операции)
- [ ] Unit + integration тесты

### Этап 6: API Layer (3–4 недели)
- [ ] FastAPI/Litestar приложение, middleware, DI
- [ ] Все REST-эндпоинты (users, services, billing, payments, spool, events, config, webhooks)
- [ ] WebSocket уведомления
- [ ] OpenAPI документация (автогенерация)
- [ ] Pydantic-схемы (request/response validation)
- [ ] Error handling, idempotency

### Этап 7: Admin Panel (3–4 недели)
- [ ] React/Next.js frontend
- [ ] Dashboard, управление пользователями, тарифами, платежами
- [ ] Мониторинг очереди задач (spool)
- [ ] Аудит-лог

### Этап 8: Notifications & Integrations (2–3 недели)
- [ ] Email (SMTP + шаблоны)
- [ ] SMS (интеграция с провайдером)
- [ ] Event-driven уведомления через WebSocket
- [ ] Миграция существующих email-шаблонов

### Этап 9: Observability & DevOps (2 недели)
- [ ] OpenTelemetry (tracing, metrics)
- [ ] Prometheus + Grafana
- [ ] Sentry (error tracking)
- [ ] Structured logging (structlog)
- [ ] Helm chart (обновлённый)
- [ ] Docker multi-stage builds
- [ ] Production docker-compose

### Этап 10: Tests & Hardening (2–3 недели)
- [ ] Покрытие тестами: unit >80%, integration >60%
- [ ] factory_boy фабрики
- [ ] conftest.py fixtures
- [ ] Load testing (locust)
- [ ] Security audit
- [ ] Documentation (MkDocs)

### Этап 11: Migration & Launch (2–3 недели)
- [ ] Скрипт миграции данных из старой БД
- [ ] Параллельный запуск (blue-green)
- [ ] Feature flags для постепенного переключения
- [ ] Rollback-план
- [ ] Go-live! 🚀