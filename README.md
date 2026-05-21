# SHM Next — Современная биллинговая система

**Современная система управления абонентами и биллингом** для интернет-провайдеров и телеком-компаний.

![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![Next.js](https://img.shields.io/badge/Next.js-14-000000)
![Litestar](https://img.shields.io/badge/Litestar-3.0-FF6B6B)
![Docker](https://img.shields.io/badge/Docker-2496ED)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Ключевые возможности

- Чистая **DDD-архитектура** (Domain-Driven Design)
- Высокопроизводительный **Async API** на Litestar
- Мощный **Worker** (Taskiq) + Spool-система с retry
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

*Скриншоты будут добавлены после деплоя*

## 🏗️ Архитектура

```
shm-next/
├── app/        — Backend (Litestar + DDD)
├── admin/      — Admin Panel (Next.js)
└── app/worker/ — Фоновые задачи
```

## 📄 Лицензия

Проект распространяется под лицензией MIT — см. [LICENSE](LICENSE).

## 🗺️ Roadmap

- **v0.2.0** — Улучшения Admin Panel + Rate Limiting
- **v0.3.0** — Security + Performance
- **v1.0.0** — Multi-tenancy и расширенная аналитика
