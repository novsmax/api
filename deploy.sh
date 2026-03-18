#!/bin/bash
set -e

echo "Останавливаем контейнер..."
docker stop smarttracker-api 2>/dev/null || true
docker rm smarttracker-api 2>/dev/null || true

echo "Собираем образ..."
docker build -t smarttracker-api .

echo "Запускаем контейнер..."
docker run -d \
  --name smarttracker-api \
  --env-file ~/api/.env \
  --dns 8.8.8.8 \
  -p 8000:8000 \
  smarttracker-api

echo "Логи:"
sleep 2
docker logs smarttracker-api --tail 20