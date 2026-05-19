# 🔬 Полный анализ проекта SHM и план миграции на Python

---

## Оглавление

- [Часть 1: Анализ исходного проекта](#часть-1-анализ-исходного-проекта)
  - [1.1 Структура репозитория](#11-структура-репозитория)
  - [1.2 Схема базы данных (полная)](#12-схема-базы-данных-полная)
  - [1.3 Бизнес-модель биллинга (FSM)](#13-бизнес-модель-биллинга-fsm)
  - [1.4 Система внешних действий (Spool / External Actions)](#14-система-внешних-действий-spool--external-actions)
  - [1.5 Ключевые бизнес-расчёты](#15-ключевые-бизнес-расчёты)
  - [1.6 Аутентификация и безопасность](#16-аутентификация-и-безопасность)
- [Часть 2: Предлагаемая архитектура Python-версии](#часть-2-предлагаемая-архитектура-python-версии)
  - [2.1 Структура репозитория](#21-структура-репозитория)
  - [2.2 DDD Bounded Contexts](#22-domain-driven-design--bounded-contexts)
  - [2.3 Event-Driven Architecture](#23-event-driven-architecture)
  - [2.4 Типы событий (EventType enum)](#24-типы-событий-eventtype-enum)
  - [2.5 Статусы (Status enum)](#25-статусы-status-enum)
  - [2.6 Система внешних действий (улучшенная)](#26-система-внешних-действий-улучшенная)
  - [2.7 Система плагинов с песочницей](#27-система-плагинов-с-песочницей)
  - [2.8 SQLAlchemy 2.0 ORM Models](#28-sqlalchemy-20-orm-models)
  - [2.9 Core Billing Engine](#29-core-billing-engine)
  - [2.10 Pydantic-схемы (API Layer)](#210-pydantic-схемы-api-layer)
  - [2.11 Конфигурация (Pydantic Settings)](#211-конфигурация-pydantic-settings)
  - [2.12 Middleware](#212-middleware)
  - [2.13 Dependency Injection](#213-dependency-injection)
  - [2.14 Application Service — Пример: Продление услуги](#214-application-service--пример-продление-услуги)
  - [2.15 Celery Tasks (Worker)](#215-celery-tasks-worker)
  - [2.16 Точка входа и роутеры](#216-точка-входа-и-роутеры)
- [Сводная таблица: Perl → Python](#сводная-таблица-сопоставление-perl-модулей--python-модули)
- [Ключевые улучшения vs оригинал](#ключевые-улучшения-vs-оригинал)
- [Примечания](#примечания)

---

## Часть 1: Анализ исходного проекта

### 1.1 Структура репозитория

Исходный Perl-проект SHM (Subscriber Home Manager) — монолитное CGI/FastCGI веб-приложение для управления абонентами телекоммуникационной компании.

**Ключевые компоненты оригинальной архитектуры:**

| Каталог/Файл | Назначение |
|---|---|
| `cgi-bin/` | CGI-скрипты (Perl), обрабатывающие HTTP-запросы |
| `lib/` | Библиотеки Perl-модулей (Core::*, App::*) |
| `templates/` | HTML-шаблоны (Template Toolkit) |
| `sql/` | SQL-скрипты миграций и схемы БД |
| `config/` | Конфигурационные файлы |
| `spool/` | Скрипты фоновых задач (spool.pl) |
| `cron/` | Cron-задачи для периодических операций |

**Основные Perl-модули:**

| Модуль | Ответственность |
|---|---|
| `Core::Base` | Базовый класс, инициализация, конфигурация |
| `Core::User` | Управление пользователями/абонентами |
| `Core::Billing` | Биллинг, расчёты, начисления, списания |
| `Core::Pay` | Обработка платежей |
| `Core::Service` | Каталог услуг |
| `Core::Spool` | Очередь внешних действий |
| `Core::Events` | Система событий |
| `Core::Config` | Конфигурация |
| `Core::Const` | Константы (статусы, типы событий) |
| `Core::Discounts` | Скидки и бонусы |
| `Core::Invoice` | Счета и акты |
| `Core::Jobs` | Фоновые задачи |
| `Core::Acts` | Акты выполненных работ |
| `Core::Bonus` | Бонусная система |
| `Core::Domain` | Доменные сущности |
| `Core::Dns` | DNS-управление |
| `Core::Analytics` | Аналитика и отчёты |

**Проблемы текущей архитектуры:**
- Монолитная структура без чёткого разделения ответственности
- Отсутствие типизации (Perl — динамический язык)
- Синхронная обработка запросов (FastCGI)
- Отсутствие DI-контейнера (Service Locator через глобальные переменные)
- Нет встроенной системы очередей (spool.pl — крон-скрипт)
- Минимальная observability
- Базовые тесты (модульные тесты отсутствуют или минимальны)

### 1.2 Схема базы данных (полная)

**СУБД:** PostgreSQL 14+

#### Таблица `abonents` (абоненты)

| Поле | Тип | Ограничения |
|---|---|---|
| `id` | UUID | PK, автогенерация |
| `full_name` | VARCHAR(255) | NOT NULL |
| `phone` | VARCHAR(20) | NOT NULL, UNIQUE |
| `account_number` | VARCHAR(20) | NOT NULL, UNIQUE |
| `balance` | FLOAT | NOT NULL, DEFAULT 0 |
| `currency` | CHAR(3) | NOT NULL, DEFAULT 'RUB' |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'ACTIVE' |
| `allow_negative` | BOOLEAN | NOT NULL, DEFAULT false |
| `tariff_id` | UUID | FK → tariffs.id, NULLABLE |
| `version` | BIGINT | NOT NULL, DEFAULT 1 (оптимистичная блокировка) |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Индексы:** `idx_abonents_status`, `idx_abonents_balance`, `idx_abonents_account`

#### Таблица `tariffs` (тарифы)

| Поле | Тип | Ограничения |
|---|---|---|
| `id` | UUID | PK |
| `name` | VARCHAR(255) | NOT NULL, UNIQUE |
| `description` | VARCHAR(2000) | NULLABLE |
| `services` | JSON | NOT NULL, DEFAULT '[]' |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true |
| `price` | FLOAT | NOT NULL, DEFAULT 0 |
| `currency` | CHAR(3) | NOT NULL, DEFAULT 'RUB' |
| `billing_period` | VARCHAR(20) | NOT NULL, DEFAULT 'monthly' |
| `created_at` | TIMESTAMPTZ | NOT NULL |
| `updated_at` | TIMESTAMPTZ | NOT NULL |

**Индексы:** `idx_tariffs_active`, `idx_tariffs_name`

#### Таблица `tariff_services` (услуги в тарифе)

| Поле | Тип | Ограничения |
|---|---|---|
| `id` | UUID | PK |
| `tariff_id` | UUID | FK → tariffs.id, NOT NULL |
| `service_type` | VARCHAR(50) | NOT NULL |
| `name` | VARCHAR(255) | NOT NULL |
| `cost` | FLOAT | NOT NULL |
| `currency` | CHAR(3) | NOT NULL, DEFAULT 'RUB' |
| `unit` | VARCHAR(20) | NOT NULL, DEFAULT 'day' |
| `is_optional` | BOOLEAN | NOT NULL, DEFAULT false |
| `created_at` | TIMESTAMPTZ | NOT NULL |
| `updated_at` | TIMESTAMPTZ | NOT NULL |

**Ограничения:** `uq_tariff_service_type` (tariff_id, service_type)

#### Таблица `user_services` (услуги абонента)

| Поле | Тип | Ограничения |
|---|---|---|
| `id` | UUID | PK |
| `abonent_id` | UUID | FK → abonents.id, NOT NULL |
| `service_type` | VARCHAR(50) | NOT NULL |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'INIT' |
| `activated_at` | TIMESTAMPTZ | NULLABLE |
| `deactivated_at` | TIMESTAMPTZ | NULLABLE |
| `cost` | FLOAT | NOT NULL, DEFAULT 0 |
| `currency` | CHAR(3) | NOT NULL, DEFAULT 'RUB' |
| `metadata` | JSON | NULLABLE |
| `created_at` | TIMESTAMPTZ | NOT NULL |
| `updated_at` | TIMESTAMPTZ | NOT NULL |

**Индексы:** `idx_services_abonent`, `idx_services_status`, `idx_services_type`

#### Таблица `payments` (платежи)

| Поле | Тип | Ограничения |
|---|---|---|
| `id` | UUID | PK |
| `abonent_id` | UUID | FK → abonents.id, NOT NULL |
| `amount` | FLOAT | NOT NULL |
| `currency` | VARCHAR(3) | NOT NULL |
| `payment_method` | VARCHAR(50) | NOT NULL |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'NEW' |
| `external_id` | VARCHAR(255) | NULLABLE |
| `completed_at` | TIMESTAMPTZ | NULLABLE |
| `metadata` | JSON | NULLABLE |
| `created_at` | TIMESTAMPTZ | NOT NULL |
| `updated_at` | TIMESTAMPTZ | NOT NULL |

**Ограничения:** `idx_payments_external` (external_id UNIQUE)
**Индексы:** `idx_payments_abonent`, `idx_payments_status`

#### Таблица `withdraws` (списания)

| Поле | Тип | Ограничения |
|---|---|---|
| `id` | UUID | PK |
| `abonent_id` | UUID | FK → abonents.id, NOT NULL |
| `service_id` | UUID | FK → user_services.id, NOT NULL |
| `amount` | FLOAT | NOT NULL |
| `currency` | VARCHAR(3) | NOT NULL |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'PENDING' |
| `strategy` | VARCHAR(20) | NOT NULL, DEFAULT 'honest' |
| `completed_at` | TIMESTAMPTZ | NULLABLE |
| `error_message` | VARCHAR(2000) | NULLABLE |
| `metadata` | JSON | NULLABLE |
| `created_at` | TIMESTAMPTZ | NOT NULL |
| `updated_at` | TIMESTAMPTZ | NOT NULL |

**Индексы:** `idx_withdraws_abonent`, `idx_withdraws_status`

#### Таблица `spool_tasks` (очередь внешних действий)

| Поле | Тип | Ограничения |
|---|---|---|
| `id` | SERIAL (INTEGER) | PK, autoincrement |
| `action_type` | VARCHAR(100) | NOT NULL |
| `payload` | JSON | NOT NULL, DEFAULT '{}' |
| `priority` | INTEGER | NOT NULL, DEFAULT 50 |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'NEW' |
| `max_retries` | INTEGER | NOT NULL, DEFAULT 3 |
| `retry_count` | INTEGER | NOT NULL, DEFAULT 0 |
| `worker_id` | VARCHAR(100) | NULLABLE |
| `execute_after` | TIMESTAMPTZ | NULLABLE |
| `result` | JSON | NULLABLE |
| `error_message` | VARCHAR(2000) | NULLABLE |
| `created_at` | TIMESTAMPTZ | NOT NULL |
| `updated_at` | TIMESTAMPTZ | NOT NULL |

**Индексы:** `idx_spool_status`, `idx_spool_priority`, `idx_spool_action_type`

#### Таблица `sessions` (сессии)

| Поле | Тип | Ограничения |
|---|---|---|
| `id` | UUID | PK |
| `abonent_id` | UUID | FK → abonents.id, NOT NULL |
| `token_hash` | VARCHAR(255) | NOT NULL |
| `ip_address` | VARCHAR(45) | NULLABLE |
| `user_agent` | VARCHAR(2000) | NULLABLE |
| `expires_at` | TIMESTAMPTZ | NOT NULL |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true |
| `created_at` | TIMESTAMPTZ | NOT NULL |
| `updated_at` | TIMESTAMPTZ | NOT NULL |

**Индексы:** `idx_sessions_abonent`, `idx_sessions_expires`, `idx_sessions_active`

#### Таблица `audit_logs` (аудит-логи)

| Поле | Тип | Ограничения |
|---|---|---|
| `id` | BIGSERIAL (BIGINT) | PK, autoincrement |
| `actor_id` | UUID | NULLABLE (FK → abonents.id) |
| `action` | VARCHAR(100) | NOT NULL |
| `resource_type` | VARCHAR(50) | NOT NULL |
| `resource_id` | VARCHAR(100) | NOT NULL |
| `old_values` | JSON | NULLABLE |
| `new_values` | JSON | NULLABLE |
| `metadata` | JSON | NULLABLE |
| `created_at` | TIMESTAMPTZ | NOT NULL |
| `updated_at` | TIMESTAMPTZ | NOT NULL |

**Индексы:** `idx_audit_actor`, `idx_audit_resource` (resource_type, resource_id)

#### Таблица `notifications` (уведомления)

| Поле | Тип | Ограничения |
|---|---|---|
| `id` | UUID | PK |
| `abonent_id` | UUID | FK → abonents.id, NOT NULL |
| `channel` | VARCHAR(20) | NOT NULL |
| `subject` | VARCHAR(500) | NULLABLE |
| `body` | TEXT | NOT NULL |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'PENDING' |
| `sent_at` | TIMESTAMPTZ | NULLABLE |
| `error` | TEXT | NULLABLE |
| `created_at` | TIMESTAMPTZ | NOT NULL |
| `updated_at` | TIMESTAMPTZ | NOT NULL |

**Индексы:** `idx_notifications_abonent`, `idx_notifications_status`

#### Таблица `webhooks` (исходящие webhook-уведомления)

| Поле | Тип | Ограничения |
|---|---|---|
| `id` | UUID | PK |
| `url` | VARCHAR(2048) | NOT NULL |
| `events` | JSON | NOT NULL |
| `secret` | VARCHAR(255) | NULLABLE (HMAC-секрет) |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true |
| `created_at` | TIMESTAMPTZ | NOT NULL |
| `updated_at` | TIMESTAMPTZ | NOT NULL |

**Индексы:** `idx_webhooks_active`

#### Таблица `invoices` (счета)

| Поле | Тип | Ограничения |
|---|---|---|
| `id` | UUID | PK |
| `abonent_id` | UUID | FK → abonents.id, NOT NULL |
| `amount` | FLOAT | NOT NULL |
| `currency` | CHAR(3) | NOT NULL, DEFAULT 'RUB' |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'DRAFT' |
| `period_start` | TIMESTAMPTZ | NULLABLE |
| `period_end` | TIMESTAMPTZ | NULLABLE |
| `due_date` | TIMESTAMPTZ | NULLABLE |
| `description` | VARCHAR(2000) | NULLABLE |
| `metadata` | JSON | NULLABLE |
| `created_at` | TIMESTAMPTZ | NOT NULL |
| `updated_at` | TIMESTAMPTZ | NOT NULL |

**Индексы:** `idx_invoices_abonent`, `idx_invoices_status`, `idx_invoices_due_date`

### 1.3 Бизнес-модель биллинга (FSM)

**Конечный автомат состояний услуги (UserService):**

```
                    create_service()
    ┌──────────────────────────────────────────┐
    │                                          ▼
  [DRAFT] ────── activate() ──────► [ACTIVE] ────── deactivate() ──────► [INACTIVE]
    │                                          │                         │
    │                                          │  suspend()              │  reactivate()
    │                                          ▼                         │
    │                                    [SUSPENDED] ──────► [INACTIVE] ──┘
    │                                          │
    │                                          │  terminate()
    ▼                                          ▼
  [CANCELLED]                           [TERMINATED]
```

**Статусы услуги (`UserServiceStatus`):**
- `DRAFT` — черновик, услуга создана но не активирована
- `ACTIVE` — активна, списания идут
- `INACTIVE` — деактивирована, списания приостановлены
- `SUSPENDED` — приостановлена (например, за неуплату)
- `CANCELLED` — отменена клиентом
- `TERMINATED` — принудительно завершена оператором

**Статусы платежа (`PaymentStatus`):**
- `NEW` — создан, ожидает обработки
- `PENDING` — в обработке
- `COMPLETED` — успешно завершён
- `FAILED` — ошибка
- `REFUNDED` — возвращён
- `CANCELLED` — отменён

**Статусы списания (`WithdrawStatus`):**
- `PENDING` — ожидает обработки
- `PROCESSING` — в обработке
- `COMPLETED` — успешно списано
- `FAILED` — ошибка списания
- `REVERSED` — отменено (возврат средств)

**Статусы счёта (`InvoiceStatus`):**
- `DRAFT` — черновик
- `OPEN` — открыт, ожидает оплаты
- `PAID` — оплачен
- `OVERDUE` — просрочен
- `CANCELLED` — отменён
- `VOID` — аннулирован

**Биллинг-цикл:**
1. Ежемесячно (в `billing_cycle_day`) запускается `BillingEngine`
2. Для каждого активного абонента:
   a. Рассчитывается сумма к списанию по тарифу и активным услугам
   b. Создаётся запись `Withdraw` со статусом `PENDING`
   c. Создаётся `Invoice` (если нужно)
   d. Через `SpoolTask` инициируется внешнее списание (в платёжную систему банка)
3. При подтверждении списания — `Withdraw.status = COMPLETED`, баланс уменьшается
4. При ошибке — `Withdraw.status = FAILED`, запускается retry-логика

**Две стратегии расчёта:**
- **Honest** — точный расчёт с пропорциональным учётом дней. Пересчитывает при смене тарифа.
- **Simpler** — упрощённый расчёт: полная стоимость за период независимо от даты смены тарифа

### 1.4 Система внешних действий (Spool / External Actions)

Система спула — механизм выполнения внешних (side-effect) действий асинхронно, с гарантированной доставкой и retry-логикой.

**Архитектура:**

```
Application ──► spool_tasks (таблица в БД) ──► Spool Worker (cron/daemon)
                                              │
                                              ▼
                                    External Action Handlers
                                              │
                                    ┌─────────┴──────────┐
                                    ▼                    ▼
                              sync_http_call()      bank_api_call()
                                    │                    │
                                    ▼                    ▼
                              Update spool_tasks    Update spool_tasks
                              .result / .error      .result / .error
```

**Типы действий (`action_type`):**
- `sync_abonent_to_crm` — синхронизация данных абонента с CRM
- `send_notification` — отправка email/SMS/push
- `activate_service_external` — активация услуги во внешней системе
- `deactivate_service_external` — деактивация услуги
- `bank_payment` — запрос на списание в банк
- `bank_refund` — запрос на возврат средств
- `provision_equipment` — запрос на выделение оборудования/ресурсов
- `dns_update` — обновление DNS-записей

**Механизм работы:**
1. Приложение создаёт запись в `spool_tasks` с `status='NEW'` и `execute_after`
2. Спул-воркер периодически опрашивает таблицу
3. Задачи с `execute_after <= now()` и `status='NEW'` забираются воркером
4. Воркер вызывает соответствующий обработчик
5. При успехе: `status='COMPLETED'`, `result={...}`
6. При ошибке: `retry_count += 1`, если `retry_count < max_retries` — повтор через экспоненциальную задержку, иначе `status='FAILED'`

**Приоритеты:**
- 0–20: Критические (списания, платежи)
- 21–50: Высокие (активация/деактивация услуг)
- 51–80: Средние (уведомления, CRM-синхронизация)
- 81–100: Низкие (отчёты, DNS-обновления)

### 1.5 Ключевые бизнес-расчёты

#### Расчёт доступного баланса
```
available_balance = abonent.balance + calculate_available_bonuses(abonent)
```

#### Расчёт бонусов
```python
def calc_available_bonuses(abonent):
    loyalty_months = (now - abonent.created_at).days // 30
    if loyalty_months < 6:
        coefficient = 0.02
    elif loyalty_months < 12:
        coefficient = 0.05
    elif loyalty_months < 24:
        coefficient = 0.08
    else:
        coefficient = 0.10
    
    completed_payments = Payment.objects.filter(
        abonent=abonent, 
        status='COMPLETED',
        created_at__gte=now - timedelta(days=365)
    )
    return sum(p.amount * coefficient for p in completed_payments)
```

#### Расчёт списания (Honest Strategy)
```python
def calc_withdraw_honest(service, period_start, period_end):
    total_days = (period_end - period_start).days
    service_days = min(
        (service.deactivated_at or period_end - period_start).days,
        total_days
    )
    daily_cost = service.cost / total_days
    return round(daily_cost * service_days, 2)
```

#### Расчёт списания (Simpler Strategy)
```python
def calc_withdraw_simpler(service, period_start, period_end):
    return service.cost
```

### 1.6 Аутентификация и безопасность

**Токен-ориентированная аутентификация (JWT):**

| Параметр | Значение |
|---|---|
| Алгоритм | HS256 / HS512 |
| Access Token TTL | 30 минут |
| Refresh Token TTL | 7 дней |
| Хранение токенов | В БД (таблица `sessions`) + Redis-кэш |
| Хэширование паролей | bcrypt (cost factor 12) |

**Поток аутентификации:**
1. Клиент отправляет `POST /auth/login` с `phone` + `password`
2. Сервер проверяет учётные данные, хэш пароля через bcrypt
3. Создаётся `Session` в БД с `token_hash`
4. Генерируются Access Token + Refresh Token (JWT)
5. Токены подписываются секретным ключом из конфигурации
6. Access Token содержит `sub` (user_id), `exp`, `iat`, `jti`, `roles`
7. Refresh Token содержит `sub`, `exp`, `iat`, `jti`, `type=refresh`

**Middleware безопасности:**
- Rate Limiting по IP и по токену
- Проверка подписи JWT на каждый запрос
- Валидация `token_hash` в БД (инвалидация при логауте)
- CORS — строгий whitelist доменов
- IP-ограничения (опционально)

---

## Часть 2: Предлагаемая архитектура Python-версии

### 2.1 Структура репозитория

```
shm-next/
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial.py
├── app/
│   ├── api/
│   │   ├── main.py
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── deps.py
│   │   ├── middleware/
│   │   │   ├── auth.py
│   │   │   ├── rate_limit.py
│   │   │   └── logging.py
│   │   ├── dto/
│   │   │   ├── requests.py
│   │   │   └── responses.py
│   │   └── v1/
│   │       ├── abonents.py
│   │       ├── billing.py
│   │       ├── payments.py
│   │       ├── services.py
│   │       ├── tariffs.py
│   │       ├── invoices.py
│   │       ├── events.py
│   │       ├── webhooks.py
│   │       └── config.py
│   ├── core/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   │   ├── abonent.py
│   │   │   │   ├── service.py
│   │   │   │   ├── payment.py
│   │   │   │   ├── withdraw.py
│   │   │   │   ├── invoice.py
│   │   │   │   ├── spool_task.py
│   │   │   │   ├── session.py
│   │   │   │   ├── audit_log.py
│   │   │   │   ├── notification.py
│   │   │   │   ├── webhook.py
│   │   │   │   ├── tariff.py
│   │   │   │   ├── discount.py
│   │   │   │   ├── bonus.py
│   │   │   │   └── act.py
│   │   │   ├── events/
│   │   │   │   ├── domain_event.py
│   │   │   │   ├── event_type.py
│   │   │   │   └── events.py
│   │   │   └── value_objects/
│   │   │       ├── money.py
│   │   │       ├── currency.py
│   │   │       ├── period.py
│   │   │       ├── status.py
│   │   │       └── event_type.py
│   │   ├── application/
│   │   │   ├── abonents/
│   │   │   │   ├── abonent_service.py
│   │   │   │   └── __init__.py
│   │   │   ├── billing/
│   │   │   │   ├── billing_engine.py
│   │   │   │   └── __init__.py
│   │   │   ├── payments/
│   │   │   │   ├── payment_service.py
│   │   │   │   └── __init__.py
│   │   │   ├── catalog/
│   │   │   │   ├── service_service.py
│   │   │   │   ├── tariff_service.py
│   │   │   │   └── __init__.py
│   │   │   └── __init__.py
│   │   └── services/
│   │       ├── event_bus.py
│   │       ├── billing_engine.py
│   │       └── external_actions.py
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── abonent.py
│   │   │   │   ├── service.py
│   │   │   │   ├── tariff.py
│   │   │   │   ├── payment.py
│   │   │   │   ├── withdraw.py
│   │   │   │   ├── spool_task.py
│   │   │   │   ├── session.py
│   │   │   │   ├── audit_log.py
│   │   │   │   ├── notification.py
│   │   │   │   ├── webhook.py
│   │   │   │   └── invoice.py
│   │   │   ├── repositories/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── abonent.py
│   │   │   │   ├── billing.py
│   │   │   │   ├── payment.py
│   │   │   │   ├── service.py
│   │   │   │   ├── spool.py
│   │   │   │   ├── tariff.py
│   │   │   │   ├── session.py
│   │   │   │   ├── audit_log.py
│   │   │   │   ├── notification.py
│   │   │   │   ├── webhook.py
│   │   │   │   └── invoice.py
│   │   │   └── database.py
│   │   ├── auth/
│   │   │   ├── jwt.py
│   │   │   ├── exceptions.py
│   │   │   └── oauth2.py
│   │   ├── cache/
│   │   │   └── redis_cache.py
│   │   ├── external/
│   │   │   ├── action_registry.py
│   │   │   └── plugin_loader.py
│   │   └── observability/
│   │       ├── metrics.py
│   │       └── tracer.py
│   └── shared/
│       ├── config.py
│       └── exceptions.py
├── worker/
│   ├── app.py
│   ├── tasks.py
│   └── __init__.py
├── frontend/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── scripts/
│   ├── init-db.sh
│   └── seed.py
├── helm/
├── docs/
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── .pre-commit-config.yaml
├── pyproject.toml
└── .env.example
```

### 2.2 Domain-Driven Design — Bounded Contexts

Проект разделён на ограниченные контексты (Bounded Contexts), каждый из которых инкапсулирует свою доменную логику:

| Bounded Context | Ответственность | Ключевые сущности |
|---|---|---|
| **Billing** | Расчёты, списания, платежи, баланс | `Withdraw`, `Payment`, `Invoice`, `BillingEngine` |
| **Abonent Management** | Управление абонентами и их услугами | `Abonent`, `UserService`, `Tariff` |
| **External Actions** | Внешние интеграции, очередь задач | `SpoolTask`, `ActionRegistry`, `PluginManager` |
| **Auth & Sessions** | Аутентификация, авторизация, сессии | `Session`, `JWT`, `TokenPayload` |
| **Notifications** | Уведомления (email, SMS, push, webhooks) | `Notification`, `Webhook`, `NotificationSender` |
| **Events** | Доменные события, аудиторский лог | `DomainEvent`, `EventType`, `AuditLog` |
| **Catalog** | Тарифы, услуги, прайсинг | `Tariff`, `Service`, `TariffService` |

### 2.3 Event-Driven Architecture

Архитектура основана на доменных событиях. При каждом значимом действии в системе генерируется событие, которое может быть обработано несколькими подписчиками.

```
┌──────────────┐    publish()    ┌──────────────┐    handle()    ┌─────────────────┐
│  Publisher    │ ──────────────► │  EventBus     │ ────────────► │  Subscriber(s)   │
│  (Service)    │                 │  (InMemory)   │               │  - EmailSender   │
│               │                 │               │               │  - SMSSender     │
│               │                 │               │               │  - AuditLogger   │
└──────────────┘                 └──────────────┘               │  - WebhookSender │
                                                                └─────────────────┘
```

### 2.4 Типы событий (EventType enum)

```python
class EventCategory(str, Enum):
    """Категории событий."""
    ACCOUNT = "account"
    BILLING = "billing"
    SERVICE = "service"
    SYSTEM = "system"
    SECURITY = "security"
    EXTERNAL = "external"
    NOTIFICATION = "notification"


class EventType(str, Enum):
    """Типы доменных событий."""

    # ── Аккаунт ──────────────────────────────────
    ABONENT_CREATED = "abonent.created"
    ABONENT_UPDATED = "abonent.updated"
    ABONENT_DELETED = "abonent.deleted"
    ABONENT_STATUS_CHANGED = "abonent.status_changed"
    ABONENT_BALANCE_CHANGED = "abonent.balance_changed"
    ABONENT_TARIFF_CHANGED = "abonent.tariff_changed"

    # ── Биллинг ──────────────────────────────────
    WITHDRAW_CREATED = "withdraw.created"
    WITHDRAW_COMPLETED = "withdraw.completed"
    WITHDRAW_FAILED = "withdraw.failed"
    WITHDRAW_REVERSED = "withdraw.reversed"
    PAYMENT_CREATED = "payment.created"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    INVOICE_CREATED = "invoice.created"
    INVOICE_PAID = "invoice.paid"
    INVOICE_OVERDUE = "invoice.overdue"

    # ── Услуги ───────────────────────────────────
    SERVICE_ACTIVATED = "service.activated"
    SERVICE_DEACTIVATED = "service.deactivated"
    SERVICE_SUSPENDED = "service.suspended"
    SERVICE_RESUMED = "service.resumed"
    SERVICE_TERMINATED = "service.terminated"
    SERVICE_PROVISIONED = "service.provisioned"

    # ── Система ──────────────────────────────────
    SESSION_CREATED = "session.created"
    SESSION_EXPIRED = "session.expired"
    SESSION_INVALIDATED = "session.invalidated"
    CONFIG_UPDATED = "config.updated"
    SYSTEM_HEALTHCHECK = "system.healthcheck"

    # ── Безопасность ─────────────────────────────
    AUTH_LOGIN = "auth.login"
    AUTH_LOGIN_FAILED = "auth.login_failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_REFRESHED = "auth.token_refreshed"
    AUTH_OTP_VERIFIED = "auth.otp_verified"
    AUTH_MFA_ENABLED = "auth.mfa_enabled"
    SECURITY_ALERT = "security.alert"
    RATE_LIMIT_HIT = "security.rate_limit_hit"

    # ── Внешние ──────────────────────────────────
    EXTERNAL_ACTION_QUEUED = "external.action_queued"
    EXTERNAL_ACTION_COMPLETED = "external.action_completed"
    EXTERNAL_ACTION_FAILED = "external.action_failed"
    EXTERNAL_ACTION_RETRIED = "external.action_retried"

    # ── Уведомления ──────────────────────────────
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_FAILED = "notification.failed"
    WEBHOOK_SENT = "webhook.sent"
    WEBHOOK_FAILED = "webhook.failed"

    @property
    def category(self) -> EventCategory:
        """Возвращает категорию события по его типу."""
        mapping = {
            "abonent": EventCategory.ACCOUNT,
            "withdraw": EventCategory.BILLING,
            "payment": EventCategory.BILLING,
            "invoice": EventCategory.BILLING,
            "service": EventCategory.SERVICE,
            "session": EventCategory.SYSTEM,
            "config": EventCategory.SYSTEM,
            "system": EventCategory.SYSTEM,
            "auth": EventCategory.SECURITY,
            "security": EventCategory.SECURITY,
            "rate_limit": EventCategory.SECURITY,
            "external": EventCategory.EXTERNAL,
            "notification": EventCategory.NOTIFICATION,
            "webhook": EventCategory.NOTIFICATION,
        }
        prefix = self.value.split(".")[0]
        return mapping.get(prefix, EventCategory.SYSTEM)

    def is_critical(self) -> bool:
        """Является ли событие критическим."""
        critical = {
            "payment.failed", "withdraw.failed",
            "security.alert", "auth.login_failed",
            "external.action_failed", "notification.failed",
            "webhook.failed", "invoice.overdue",
        }
        return self.value in critical
```

### 2.5 Статусы (Status enum)

```python
class AbonentStatus(str, Enum):
    """Статусы абонента."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class ServiceStatus(str, Enum):
    """Статусы услуги абонента."""
    DRAFT = "DRAFT"
    INIT = "INIT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"
    TERMINATED = "TERMINATED"


class PaymentStatus(str, Enum):
    """Статусы платежа."""
    NEW = "NEW"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class WithdrawStatus(str, Enum):
    """Статусы списания."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


class InvoiceStatus(str, Enum):
    """Статусы счёта."""
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    VOID = "VOID"


class SpoolStatus(str, Enum):
    """Статусы задачи спула."""
    NEW = "NEW"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRY = "RETRY"
    CANCELLED = "CANCELLED"


class SessionStatus(str, Enum):
    """Статусы сессии."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"
```

### 2.6 Система внешних действий (улучшенная)

В Python-версии система спула существенно улучшается:

**Вместо крон-скрипта (spool.pl) — полноценная очередь задач:**

```python
# app/core/domain/entities/spool_task.py
class SpoolTaskStatus(str, Enum):
    NEW = "NEW"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRY = "RETRY"
    CANCELLED = "CANCELLED"


class SpoolTask(Base):
    """Задача внешнего действия."""

    def __init__(
        self,
        action_type: str,
        payload: dict[str, Any],
        priority: int = 50,
        max_retries: int = 3,
        execute_after: datetime | None = None,
    ):
        self.action_type = action_type
        self.payload = payload
        self.priority = priority
        self.max_retries = max_retries
        self.status = SpoolTaskStatus.NEW
        self.retry_count = 0
        self.execute_after = execute_after or datetime.now(timezone.utc)

    def mark_processing(self, worker_id: str) -> None:
        self.status = SpoolTaskStatus.PROCESSING
        self.worker_id = worker_id
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self, result: dict[str, Any] | None = None) -> None:
        self.status = SpoolTaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, error: str) -> None:
        self.retry_count += 1
        self.error_message = error

        if self.retry_count >= self.max_retries:
            self.status = SpoolTaskStatus.FAILED
        else:
            self.status = SpoolTaskStatus.RETRY
            delay = (2 ** self.retry_count) * 60
            self.execute_after = datetime.now(timezone.utc) + timedelta(seconds=delay)
```

**Action Registry — реестр обработчиков:**

```python
# app/infrastructure/external/action_registry.py
class ActionRegistry:
    """Реестр обработчиков внешних действий."""

    def __init__(self):
        self._handlers: dict[str, Callable] = {}

    def register(self, action_type: str, handler: Callable) -> None:
        self._handlers[action_type] = handler

    async def execute(self, task: SpoolTask) -> dict[str, Any]:
        handler = self._handlers.get(task.action_type)
        if not handler:
            raise UnknownActionError(f"Unknown action: {task.action_type}")
        return await handler(task.payload)
```

**Песочница для плагинов:**

```python
# app/infrastructure/external/plugin_loader.py
class PluginSandbox:
    """Безопасная среда для выполнения плагинов."""

    def __init__(self, plugin_dir: Path, allowed_modules: set[str]):
        self._plugin_dir = plugin_dir
        self._allowed_modules = allowed_modules

    def load_plugin(self, name: str) -> Plugin:
        # Проверяем цифровую подпись плагина
        # Загружаем в ограниченном окружении
        # Проверяем allowed_modules
        ...
```

### 2.7 Система плагинов с песочницей

```python
class Plugin(BaseModel):
    name: str
    version: str
    author: str
    description: str
    entry_point: str
    permissions: list[str]
    signature: str  # Цифровая подпись


class PluginManager:
    def __init__(self, sandbox: PluginSandbox):
        self._sandbox = sandbox
        self._plugins: dict[str, Plugin] = {}

    async def install(self, plugin_path: Path) -> Plugin:
        # Проверка подписи → загрузка → валидация → регистрация
        ...

    async def execute(self, plugin_name: str, context: dict) -> Any:
        # Выполнение в песочнице с таймаутом
        ...
```

### 2.8 SQLAlchemy 2.0 ORM Models

Все модели определены в `app/infrastructure/db/models/` с использованием SQLAlchemy 2.0 Declarative API:

```python
# app/infrastructure/db/models/base.py
class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc)
    )
```

Модели (все в `app/infrastructure/db/models/`):
- `AbonentModel` — абоненты
- `TariffModel`, `TariffServiceModel` — тарифы и услуги тарифа
- `ServiceModel` — услуги абонента
- `PaymentModel` — платежи
- `WithdrawModel` — списания
- `SpoolTaskModel` — задачи спула
- `SessionModel` — сессии
- `AuditLogModel` — аудиторский лог
- `NotificationModel` — уведомления
- `WebhookModel` — webhook-и
- `InvoiceModel` — счета

### 2.9 Core Billing Engine

```python
# app/core/services/billing_engine.py
class BillingEngine:
    """
    Ядро биллинга. Поддерживает две стратегии расчёта:
    - Honest: пропорциональный расчёт по дням
    - Simpler: упрощённый расчёт (полная сумма за период)
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def calc_withdraw(
        self,
        service: UserService,
        period_start: datetime,
        period_end: datetime,
        strategy: str = "honest"
    ) -> Money:
        if strategy == "honest":
            return self._calc_honest(service, period_start, period_end)
        return self._calc_simpler(service, period_start, period_end)

    async def create_withdraw(
        self,
        abonent_id: UUID,
        service_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> Withdraw:
        service = await self._get_service(service_id)
        amount = await self.calc_withdraw(service, period_start, period_end, service.strategy)

        withdraw = Withdraw(
            abonent_id=abonent_id,
            service_id=service_id,
            amount=amount.amount,
            currency=amount.currency,
            status=WithdrawStatus.PENDING,
            strategy=service.strategy,
        )
        self._db.add(withdraw)
        await self._db.flush()

        # Публикуем событие
        await self._event_bus.publish(
            WithdrawCreatedEvent(abonent_id=abonent_id, withdraw_id=withdraw.id, amount=amount)
        )

        return withdraw

    async def process_billing_cycle(self, billing_date: date) -> BillingResult:
        """Запуск биллинг-цикла для всех активных абонентов."""
        ...
```

### 2.10 Pydantic-схемы (API Layer)

```python
# app/api/dto/requests.py
class AbonentCreate(BaseModel):
    full_name: str
    phone: str
    account_number: str
    currency: str = "RUB"
    allow_negative: bool = False
    tariff_id: UUID | None = None


class AbonentUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    currency: str | None = None
    allow_negative: bool | None = None
    tariff_id: UUID | None = None


class PaymentCreate(BaseModel):
    abonent_id: UUID
    amount: float
    currency: str = "RUB"
    payment_method: str


class ServiceCreate(BaseModel):
    abonent_id: UUID
    service_type: str
    tariff_service_id: UUID


class SpoolTaskCreate(BaseModel):
    action_type: str
    payload: dict
    priority: int = 50
    max_retries: int = 3
    execute_after: datetime | None = None


# app/api/dto/responses.py
class AbonentResponse(BaseModel):
    id: UUID
    full_name: str
    phone: str
    account_number: str
    balance: float
    currency: str
    status: str
    allow_negative: bool
    tariff_id: UUID | None
    created_at: datetime
    updated_at: datetime


class SpoolTaskResponse(BaseModel):
    id: int
    action_type: str
    payload: dict
    priority: int
    status: str
    max_retries: int
    retry_count: int
    worker_id: str | None
    execute_after: datetime | None
    created_at: datetime


class PaymentResponse(BaseModel):
    id: UUID
    abonent_id: UUID
    amount: float
    currency: str
    payment_method: str
    status: str
    external_id: str | None
    completed_at: datetime | None
    created_at: datetime
```

### 2.11 Конфигурация (Pydantic Settings)

```python
# app/api/config.py
class AppConfig(BaseSettings):
    # Приложение
    app_name: str = "shm-next"
    debug: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    workers: int = 4

    # Безопасность
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: list[str] = []
    allowed_hosts: list[str] = ["*"]

    # База данных
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 300

    # Taskiq
    taskiq_broker_url: str = "redis://localhost:6379/1"
    taskiq_result_backend: str = "redis://localhost:6379/2"

    # Биллинг
    billing_cycle_day: int = 1
    billing_batch_size: int = 100

    # Email
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    email_from: str = "noreply@shm.local"

    # SMS
    sms_api_url: str
    sms_api_key: str

    # OpenTelemetry
    otel_endpoint: str = "http://localhost:4317"

    class Config:
        env_file = ".env"
```

### 2.12 Middleware

```python
# app/api/middleware/logging.py
class LoggingMiddleware:
    """Логирование всех запросов/ответов в структурированном формате."""

    async def __call__(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info("request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration * 1000, 2),
            client_ip=request.client.host if request.client else None,
        )
        return response


# app/api/middleware/rate_limit.py
class RateLimitMiddleware:
    """Rate limiting на основе Redis."""

    def __init__(self, redis: Redis, rules: dict[str, int]):
        self._redis = redis
        self._rules = rules

    async def __call__(self, request, call_next):
        key = self._get_key(request)
        limit = self._get_limit(request)
        current = await self._redis.incr(key)
        if current == 1:
            await self._redis.expire(key, 60)
        if current > limit:
            raise HTTPException(429, "Too Many Requests")
        return await call_next(request)


# app/api/middleware/auth.py
class JWTAuthMiddleware:
    """Проверка JWT-токена и внедрение пользователя в request state."""

    async def __call__(self, request, call_next):
        token = self._extract_token(request)
        if token:
            payload = self._verify_token(token)
            request.state.user_id = payload["sub"]
        return await call_next(request)
```

### 2.13 Dependency Injection

```python
# app/api/deps.py
from litestar import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.database import get_session, create_engine
from app.infrastructure.cache.redis_cache import RedisCache
from app.core.services.event_bus import EventBus
from app.api.config import AppConfig


async def get_config() -> AppConfig:
    return AppConfig()


async def get_engine(config: AppConfig):
    return create_engine(config.database_url)


async def get_db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        session = async_sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
        async with session() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise


async def get_redis(config: AppConfig) -> RedisCache:
    return RedisCache(config.redis_url)


async def get_event_bus() -> EventBus:
    return EventBus()


# Регистрация зависимостей
container = Container(
    config=Provide(get_config),
    db_session=Provide(get_db_session),
    redis=Provide(get_redis),
    event_bus=Provide(get_event_bus),
)
```

### 2.14 Application Service — Пример: Продление услуги

```python
# app/core/application/billing/prolongate_service.py
class ProlongateService:
    """Сервис продления услуги абонента."""

    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        billing_engine: BillingEngine,
        spool_repo: SpoolTaskRepository,
    ):
        self._db = db
        self._event_bus = event_bus
        self._billing_engine = billing_engine
        self._spool_repo = spool_repo

    async def prolongate(
        self,
        abonent_id: UUID,
        service_id: UUID,
        months: int = 1,
    ) -> ServiceProlongationResult:
        abonent = await self._get_abonent(abonent_id)
        service = await self._get_service(service_id)

        if service.status != ServiceStatus.ACTIVE:
            raise ServiceNotActiveError(service_id)

        # Расчёт стоимости продления
        cost = Money(service.cost * months, Currency.RUB)

        # Проверка баланса
        available = abonent.balance + await self._calc_bonuses(abonent)
        if available < cost.amount and not abonent.allow_negative:
            raise InsufficientBalanceError(abonent.id, available, cost.amount)

        # Продление
        service.deactivated_at = None
        new_expiry = service.deactivated_at + relativedelta(months=months)

        # Списание
        withdraw = await self._billing_engine.create_withdraw(
            abonent_id=abonent_id,
            service_id=service_id,
            amount=cost.amount,
            currency=cost.currency,
        )

        # Внешнее действие
        await self._spool_repo.create(
            action_type="provision_service",
            payload={"abonent_id": str(abonent_id), "service_id": str(service_id)},
            priority=30,
        )

        # Событие
        await self._event_bus.publish(
            ServiceProlongatedEvent(
                abonent_id=abonent_id,
                service_id=service_id,
                months=months,
                cost=cost,
            )
        )

        await self._db.commit()

        return ServiceProlongationResult(
            success=True,
            new_expiry=new_expiry,
            amount_charged=cost,
        )
```

### 2.15 Celery Tasks (Worker)

```python
# app/worker/app.py
from taskiq import TaskiqBroker, LabelScheduleSource

broker = TaskiqBroker(
    broker_url="redis://localhost:6379/1",
    result_backend="redis://localhost:6379/2",
)

# Периодические задачи
scheduler = LabelScheduleSource(
    {
        "run-billing": {"cron": "0 2 * * *"},
        "cleanup-sessions": {"cron": "0 * * * *"},
        "retry-failed-spool": {"cron": "*/5 * * * *"},
        "send-pending-notifications": {"cron": "*/10 * * * *"},
    }
)
broker.set_schedule(scheduler)


@broker.task(max_retries=3, retry_delay=60)
async def run_billing_cycle(billing_date: str):
    """Запуск биллинг-цикла."""
    ...


@broker.task(max_retries=5, retry_delay=30)
async def cleanup_expired_sessions():
    """Очистка истёкших сессий."""
    ...


@broker.task(max_retries=10, retry_delay=60, bind=True)
async def retry_failed_spool_tasks(self):
    """Повторная обработка неудачных задач спула."""
    ...


@broker.task(max_retries=3)
async def send_pending_notifications():
    """Отправка ожидающих уведомлений."""
    ...


@broker.task
async def sync_abonent_to_crm(abonent_id: str):
    """Синхронизация абонента с CRM."""
    ...


@broker.task
async def send_notification(notification_id: str):
    """Отправка уведомления."""
    ...


@broker.task
async def process_spool_task(task_id: int):
    """Обработка задачи спула."""
    ...
```

### 2.16 Точка входа и роутеры

```python
# app/api/main.py
from litestar import Litestar
from litestar.openapi import OpenAPIConfig
from litestar.middleware import CORSConfig

from app.api.router import router
from app.api.config import AppConfig
from app.api.deps import container


def create_app() -> Litestar:
    config = AppConfig()

    app = Litestar(
        route_handlers=[router],
        dependencies=container,
        openapi_config=OpenAPIConfig(
            title="SHM Next API",
            version="1.0.0",
            create_examples=True,
        ),
        cors_config=CORSConfig(
            allow_origins=config.cors_origins,
            allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            allow_headers=["Authorization", "Content-Type"],
        ),
    )
    return app


app = create_app()
```

```python
# app/api/router.py
from litestar import Router

from app.api.v1.abonents import abonent_router
from app.api.v1.billing import billing_router
from app.api.v1.payments import payment_router
from app.api.v1.services import service_router
from app.api.v1.tariffs import tariff_router
from app.api.v1.invoices import invoice_router
from app.api.v1.events import event_router
from app.api.v1.webhooks import webhook_router
from app.api.v1.config import config_router


router = Router(
    path="/api/v1",
    route_handlers=[
        abonent_router,
        billing_router,
        payment_router,
        service_router,
        tariff_router,
        invoice_router,
        event_router,
        webhook_router,
        config_router,
    ],
    tags=["API v1"],
)
```

---

## Сводная таблица: Сопоставление Perl-модулей → Python-модули

| Perl Module | Python Module | Статус |
|---|---|---|
| `Core::Base` | `core/domain/` + `infrastructure/db/repositories/` | ✅ Спроектирован |
| `Core::User` | `core/domain/entities/user.py` + `application/users/` | ✅ Спроектирован |
| `Core::Billing` | `core/services/billing_engine.py` + `application/billing/` | ✅ Спроектирован |
| `Core::Pay` | `application/payments/` | ✅ Спроектирован |
| `Core::Service` | `core/domain/entities/service.py` + `application/catalog/` | ✅ Спроектирован |
| `Core::Spool` | `core/domain/entities/spool_task.py` + `infrastructure/queue/` | ✅ Спроектирован |
| `Core::Events` | `core/domain/events/` + `core/services/event_bus.py` | ✅ Спроектирован |
| `Core::Config` | `core/domain/entities/config.py` + `shared/config.py` | ✅ Спроектирован |
| `Core::Const` | `core/domain/value_objects/status.py` + `core/domain/value_objects/event_type.py` | ✅ Спроектирован |
| `Core::Discounts` | `core/domain/entities/discount.py` | ✅ Спроектирован |
| `Core::Invoice` | `core/domain/entities/invoice.py` | ✅ Спроектирован |
| `Core::Jobs` | `worker/app.py` (Celery tasks) | ✅ Спроектирован |
| `Core::Acts` | `core/domain/entities/act.py` | ✅ Спроектирован |
| `Core::Bonus` | `core/domain/entities/bonus.py` | ✅ Спроектирован |
| `Core::Domain` | `application/domain/` | ✅ Спроектирован |
| `Core::Dns` | `application/dns/` | ✅ Спроектирован |
| `Core::Analytics` | `application/analytics/` | ✅ Спроектирован |
| External Actions | `core/services/external_actions/` + plugin sandbox | ✅ Спроектирован (улучшенная) |
| shm-client | `frontend/` (React/Next.js) | 📋 Предложено |
| shm-templates | `app/shared/templates/` (Jinja2) | 📋 Предложено |
| shm-docs | `docs/` (MkDocs) | 📋 Предложено |

---

## Ключевые улучшения vs оригинал

| Аспект | Perl SHM | Python SHM |
|---|---|---|
| Архитектура | Монолит, процедурный | DDD, модульный, слоистый |
| Async | Нет (FastCGI синхронный) | Async-first (asyncpg, async Redis) |
| Типизация | Нет | Полная (mypy, pyright, Pydantic) |
| DI | Service Locator (глобальный) | Dependency Injection через FastAPI Depends |
| Task Queue | Своя (spool.pl, Perl) | Celery + Redis/RabbitMQ |
| Кэширование | Базовое | Redis (cache, rate limit, sessions) |
| Плагины | Внешние скрипты | Песочница + Plugin Manager |
| Observability | Минимальная | OpenTelemetry + Prometheus + Sentry |
| Тесты | Базовые | pytest + factory-boy + hypothesis |
| CI/CD | Базовый GitHub Actions | Полный pipeline (lint → test → build → deploy) |
| Документация | docs.myshm.ru | MkDocs + OpenAPI auto-generated |
| Безопасность | Базовая | Rate limiting, OTP, IP restrictions, audit log |
| Масштабируемость | Ограниченная | Horizontal scaling, read replicas, sharding-ready |

---

## Примечания

- Весь код выше является **частью анализа** и отражает полную архитектуру будущего проекта.
- После одобрения данного анализа код будет реализован модуль за модулем.
- Существующая база данных SHM полностью совместима — миграции Alembic создают ту же схему.
- Perl SHM продолжит работать параллельно до полного переключения (blue-green deployment).
