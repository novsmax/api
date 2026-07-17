#!/bin/bash
set -e

# docker compose v2 (плагин) либо старый docker-compose
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
else
  DC="docker-compose"
fi

# Старый деплой запускал одиночный контейнер вне compose — снимаем,
# чтобы не держал порт 8000 (после первого compose-деплоя строки не нужны)
docker stop smarttracker-api 2>/dev/null || true
docker rm smarttracker-api 2>/dev/null || true

echo "Собираем образ и поднимаем стек..."
# up перезапустит и одноразовые сервисы: postgres-migrate применит миграции
# (alembic upgrade head), cassandra-init прогонит init.cql — оба идемпотентны
$DC up -d --build

echo "Статус сервисов:"
$DC ps

echo "Логи API:"
sleep 2
$DC logs api --tail 20
