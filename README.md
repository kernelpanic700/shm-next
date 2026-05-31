# SHM Next — Современная биллинговая система

**Современная система управления абонентами и биллингом** для интернет-провайдеров и телеком-компаний.

![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![Next.js](https://img.shields.io/badge/Next.js-14-000000)
![Litestar](https://img.shields.io/badge/Litestar-2.x-FF6B6B)
![Docker](https://img.shields.io/badge/Docker-2496ED)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Ключевые возможности

- Чистая **DDD-архитектура** (Domain-Driven Design)
- Высокопроизводительный **Async API** на Litestar
- Надёжный **Worker** (Taskiq) + Spool-система с retry и backoff
- Современный **Admin Panel** на Next.js 14 + TypeScript + Recharts
- Уведомления (Email, SMS, Push, Webhooks)
- PostgreSQL + Redis

## 🚀 Быстрый старт

### Docker (рекомендуется)

```bash
git clone https://github.com/kernelpanic700/shm-next.git
cd shm-next
docker compose --profile dev up -d
```

Доступ:
- **API**: http://localhost:8001
- **OpenAPI schema/docs**: http://localhost:8001/schema
- **PostgreSQL**: localhost:15432
- **Redis**: localhost:16379

Dev-профиль Docker поднимает backend, worker, PostgreSQL и Redis. Frontend в разработке запускается локально:

```bash
# Admin Panel
cd admin
npm install
npm run dev

# Client Panel (в отдельном терминале)
cd client
npm install
npm run dev -- --port 3001
```

Локальный frontend:
- **Admin Panel**: http://localhost:3000
- **Client Panel**: http://localhost:3001

Production-профиль Docker поднимает оба интерфейса:

```bash
docker compose --profile prod up -d --build
```

Production-доступ по умолчанию:
- **API**: http://localhost:8001
- **Client Panel**: http://localhost:3001
- **Admin Panel**: http://localhost:3002

Публичная регистрация в личном кабинете управляется переменной `ENABLE_CLIENT_REGISTRATION` в `.env`:

```env
ENABLE_CLIENT_REGISTRATION=false
```

После изменения этого флага пересоберите client-образ, так как Next.js подставляет `NEXT_PUBLIC_*` настройки на этапе сборки.

### Локальный запуск

```bash
# Backend
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.api.app:app --reload --port 8001

# Admin Panel (в новом терминале)
cd admin
npm install
npm run dev
```

## 📸 Скриншоты

*Скриншоты интерфейса будут добавлены в ближайшее время*

## 🏗️ Архитектура

```
shm-next/
├── app/                    # Backend (Litestar + DDD)
├── admin/                  # Admin Panel (Next.js 14)
├── client/                 # Личный кабинет абонента (Next.js 14)
├── app/worker/             # Фоновые задачи (Taskiq)
├── tests/                  # Тесты
├── alembic/                # Миграции БД
└── docker-compose.yml
```

## 📚 Документация

- [Руководство по работе с биллингом](docs/BILLING_GUIDE.md)

## 📄 Лицензия

Проект распространяется под лицензией MIT — см. файл [LICENSE](LICENSE).

## 🤝 Contributing

Pull Request'ы приветствуются! Пожалуйста, ознакомьтесь с [CONTRIBUTING.md](CONTRIBUTING.md) для деталей.

## 🗺️ Roadmap

- **v0.2.0** — Улучшения Admin Panel + Rate Limiting
- **v0.3.0** — Security hardening + Performance
- **v1.0.0** — Multi-tenancy, расширенная аналитика, GraphQL
