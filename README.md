# SHM Next — Современная биллинговая система

**Современная система управления абонентами и биллингом** для интернет-провайдеров и телеком-компаний.

![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![Next.js](https://img.shields.io/badge/Next.js-14-000000)
![Litestar](https://img.shields.io/badge/Litestar-3.0-FF6B6B)
![Docker](https://img.shields.io/badge/Docker-2496ED)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Основные возможности

- Чистая **DDD-архитектура** (Domain-Driven Design)
- Высокопроизводительный **Async API** на Litestar
- Надёжный **Worker** на Taskiq + Spool-система с retry и backoff
- Современный **Admin Panel** на Next.js 14 + TypeScript
- Уведомления (Email, SMS, Push, Webhooks)
- PostgreSQL + Redis

## 🚀 Быстрый старт

### Docker (рекомендуется)

```bash
git clone https://github.com/kernelpanic700/shm-next.git
cd shm-next
docker compose --profile dev up -d
```

**Доступ:**
- API: http://localhost:8000
- Admin Panel: http://localhost:3000

### Локальный запуск

```bash
# Backend
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.api.app:app --reload --port 8000

# Admin Panel (в новом терминале)
cd admin
npm install
npm run dev
```

## 📸 Скриншоты

(Добавьте скриншоты в папку docs/screenshots/ после деплоя)

## 🏗️ Архитектура

```
shm-next/
├── app/                    # Backend (Litestar + DDD)
├── admin/                  # Admin Panel (Next.js 14)
├── app/worker/             # Фоновые задачи (Taskiq)
├── tests/                  # Тесты
├── alembic/                # Миграции БД
└── docker-compose.yml
```

## 📦 Технологии

- **Backend:** Python 3.12, Litestar, SQLAlchemy 2.0, Taskiq
- **Frontend:** Next.js 14, TypeScript, TanStack Query, Tailwind, shadcn/ui
- **БД:** PostgreSQL + Redis

## 📄 Лицензия

Проект распространяется под лицензией MIT — см. файл LICENSE.

## 🤝 Contributing

Pull Request'ы приветствуются!

## 🗺️ Roadmap

- **v0.2.0** — Улучшение Admin Panel + Rate Limiting
- **v0.3.0** — Security hardening + Performance
- **v1.0.0** — Multi-tenancy, расширенная аналитика, GraphQL
