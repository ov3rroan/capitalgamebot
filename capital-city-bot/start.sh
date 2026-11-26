#!/bin/bash
set -e

cd /app
export PYTHONPATH=/app/backend:${PYTHONPATH:-}
export PYTHONUNBUFFERED=1

PORT="${PORT:-8000}"
echo "==> Capital City starting on port $PORT"
echo "==> WEBAPP_URL=${WEBAPP_URL:-not set}"
if [ -n "$BOT_TOKEN" ]; then
  echo "==> BOT_TOKEN is set: yes"
else
  echo "==> BOT_TOKEN is set: NO"
fi

# Telegram-бот в фоне (если упадёт — веб продолжит работать)
(
  sleep 2
  echo "==> Starting Telegram bot..."
  python bot/main.py
) &

# FastAPI — главный процесс (Railway смотрит на него)
echo "==> Starting FastAPI..."
cd /app/backend
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
