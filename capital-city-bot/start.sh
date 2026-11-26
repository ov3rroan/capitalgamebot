#!/bin/bash
set -e

cd /app
export PYTHONPATH=/app/backend:$PYTHONPATH

echo "==> Starting Capital City on port ${PORT:-8000}"

# FastAPI (Mini App + API)
cd /app/backend
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} &
BACKEND_PID=$!

sleep 3

# Telegram bot
cd /app
python bot/main.py &
BOT_PID=$!

echo "==> Backend PID=$BACKEND_PID  Bot PID=$BOT_PID"

# Ждём, пока один из процессов не завершится
wait -n $BACKEND_PID $BOT_PID
EXIT_CODE=$?

echo "==> Process exited with $EXIT_CODE, shutting down..."
kill $BACKEND_PID $BOT_PID 2>/dev/null || true
exit $EXIT_CODE
