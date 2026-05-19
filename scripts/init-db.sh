#!/bin/bash
# Инициализация базы данных для разработки
set -euo pipefail

DB_USER="${DB_USER:-shm}"
DB_PASSWORD="${DB_PASSWORD:-shm_secret}"
DB_NAME="${DB_NAME:-shm}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

export PGPASSWORD="$DB_PASSWORD"

echo "⏳ Waiting for PostgreSQL..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q 2>/dev/null; do
  sleep 2
done

echo "✅ PostgreSQL is ready"

# Создаём БД если не существует
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME"

echo "✅ Database '$DB_NAME' is ready"
