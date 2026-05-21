# shm-next — Universal Billing System

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue?logo=docker)](https://github.com/kernelpanic700/shm-next/pkgs/container/shm-next)
[![Tests](https://img.shields.io/badge/tests-455+-green?logo=pytest)](https://github.com/kernelpanic700/shm-next/actions)
[![Release](https://img.shields.io/badge/release-v0.1.0-blue?logo=github)](https://github.com/kernelpanic700/shm-next/releases)

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
git clone https://github.com/kernelpanic700/shm-next.git
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

## 🏗️ Архитектура

```
shm-next/
├── app/                    # Основной код
│   ├── api/               # API слой (Litestar)
│   ├── core/              # Доменный слой
│   ├── infrastructure/    # Инфраструктурный слой
│   └── worker/            # Фоновые задачи (Taskiq)
├── admin/                 # Admin Panel (Next.js)
├── tests/                 # Тесты
└── docker-compose.yml     # Docker оркестрация
```

## 🧪 Тестирование

```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest tests/ --cov=app --cov-report=html
```

## 🚢 Деплой

```bash
cp .env.example .env
docker compose --profile prod up -d
```