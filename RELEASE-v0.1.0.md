# SHM Next v0.1.0 — MVP Release 🚀

Современная система биллинга с DDD-архитектурой и Admin Panel.

## Ключевые возможности

### Backend
- **Litestar API** — REST API с полным CRUD
- **DDD-архитектура** — чистый код с Value Objects, Entities
- **Taskiq Worker** — асинхронные задачи с retry/backoff
- **JWT Auth** — токены доступа и обновления
- **PostgreSQL + Redis** — основа данных

### Frontend (Admin Panel)
- **Next.js 14** — App Router + TypeScript
- **7 страниц:** Dashboard, Абоненты, Тарифы, Услуги, Платежи, SPOOL, Отчёты
- **Графики:** LineChart, PieChart, BarChart (recharts)
- **UI:** Tailwind CSS + Radix UI

## Запуск

```bash
# Backend
cp .env.example .env
docker compose --profile dev up -d

# Frontend  
cd admin && npm install && npm run dev
```

## Тесты
- 455+ тестов
- 50%+ покрытие кода

## Ссылки
- **Репозиторий:** https://github.com/kernelpanic700/shm-next
- **Документация:** README.md в репозитории