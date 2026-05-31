# SHM Next

SHM Next - биллинговая система для провайдера или небольшой телеком-команды. В проекте есть backend API, админка, личный кабинет абонента, воркер для фоновых задач и базовый контур автоматизации.

Сейчас проект удобнее рассматривать как рабочую основу: абоненты, тарифы, услуги, платежи, события и spool уже связаны между собой, но перед промышленным запуском все равно стоит пройти свои сценарии, платежные интеграции и правила доступа.

## Что внутри

- Backend на Litestar с асинхронным доступом к PostgreSQL.
- Admin Panel на Next.js для операторов и администраторов.
- Client Panel на Next.js для личного кабинета абонента.
- Taskiq worker для фоновых задач.
- Redis для очередей и кэша.
- Alembic-миграции.
- Docker Compose для локального и production-профилей.

Основные рабочие разделы админки:

- абоненты;
- тарифы;
- услуги;
- платежи и финансы;
- spool-задачи;
- автоматизация событий;
- настройки.

## Быстрый запуск

Сначала подготовьте `.env`:

```bash
cp .env.example .env
```

Минимально проверьте в нем:

- `SECRET_KEY`;
- `ADMIN_PHONE`;
- `ADMIN_PASSWORD_HASH` или временно `ADMIN_PASSWORD`;
- `API_PORT`, `CLIENT_PORT`, `ADMIN_PORT`;
- параметры PostgreSQL и Redis, если запускаете не через стандартный compose.

Production-профиль поднимает API, worker, PostgreSQL, Redis, админку и личный кабинет:

```bash
docker compose --profile prod up -d --build
```

Адреса по умолчанию:

- API: `http://localhost:8001`
- OpenAPI/schema: `http://localhost:8001/schema`
- Client Panel: `http://localhost:3001`
- Admin Panel: `http://localhost:3002`
- PostgreSQL: `localhost:15432`
- Redis: `localhost:16379`

Dev-профиль обычно используют для backend-части:

```bash
docker compose --profile dev up -d
```

Frontend в разработке удобнее запускать отдельно:

```bash
cd admin
npm install
npm run dev
```

```bash
cd client
npm install
npm run dev -- --port 3001
```

## Регистрация в личном кабинете

Публичная регистрация абонентов в Client Panel выключена по умолчанию. Это сделано намеренно: в провайдерском биллинге абоненты чаще создаются оператором, миграцией или интеграцией.

Флаг находится в `.env`:

```env
ENABLE_CLIENT_REGISTRATION=false
```

Чтобы включить регистрацию:

```env
ENABLE_CLIENT_REGISTRATION=true
```

После изменения флага нужно пересобрать client-образ, потому что Next.js подставляет публичные переменные на этапе сборки:

```bash
docker compose --profile prod build client
docker compose --profile prod up -d client
```

## Структура проекта

```text
shm-next/
├── app/                    # Backend: API, domain, application, infrastructure
├── app/worker/             # Taskiq worker и фоновые задачи
├── admin/                  # Админка
├── client/                 # Личный кабинет абонента
├── alembic/                # Миграции базы
├── docs/                   # Документация по рабочим сценариям
├── scripts/                # Вспомогательные скрипты
├── tests/                  # Unit и integration tests
└── docker-compose.yml
```

## Документация

- [Работа с биллингом](docs/BILLING_GUIDE.md)

## Проверки перед коммитом

Обычно достаточно такого набора:

```bash
.venv/bin/pytest tests/unit/api/test_abonent_controller.py -q
npm --prefix admin run lint
npm --prefix admin run build
npm --prefix client run lint
npm --prefix client run build
```

Для проверки поднятого стенда:

```bash
curl -fsS http://localhost:8001/health
docker compose ps
```

## Лицензия

Проект распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).
