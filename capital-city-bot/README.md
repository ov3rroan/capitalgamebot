# 🏙 Город Капитала — Telegram Mini App RP-игра

Полноценный MVP Telegram-бота с Mini App в жанре RP-симулятора жизни.

## Возможности

- 💼 **Работы** — 7 профессий с разным доходом, энергией и риском
- 🏠 **Имущество** — жильё, транспорт, бизнесы с пассивным доходом
- 🎰 **Казино** — слоты, рулетка, кости
- 🏆 **Топ** по капиталу
- ⚡ Система энергии и уровней
- 📈 Влияние и репутация
- Красивый тёмный неоновый интерфейс

## Структура проекта

```
capital-city-bot/
├── bot/               # Telegram-бот (aiogram 3)
│   └── main.py
├── backend/           # FastAPI + SQLite
│   ├── main.py
│   └── database.py
├── miniapp/           # Frontend Mini App
│   ├── index.html
│   ├── style.css
│   └── app.js
├── data/              # База данных (создаётся автоматически)
├── requirements.txt
├── .env.example
└── README.md
```

## Быстрый старт

### 1. Установка

```bash
cd capital-city-bot
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Создание бота

1. Напиши [@BotFather](https://t.me/BotFather) → `/newbot`
2. Получи токен
3. Скопируй `.env.example` в `.env` и вставь токен:

```bash
cp .env.example .env
# Отредактируй .env
```

### 3. Запуск Backend + Mini App

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Mini App будет доступен по адресу `http://localhost:8000`

### 4. Запуск бота

В другом терминале:

```bash
cd bot
python main.py
```

### 5. Для работы Mini App в Telegram

Telegram требует **HTTPS**. Варианты:

**Вариант A — ngrok (для теста)**
```bash
ngrok http 8000
```
Скопируй HTTPS-ссылку → вставь в `.env` как `WEBAPP_URL` и перезапусти бота.

**Вариант B — Деплой**
- Backend: Railway / Render / Fly.io
- Или весь проект на VPS с nginx + certbot

После деплоя укажи реальный `WEBAPP_URL` в `.env`.

### 6. Настройка BotFather

```
/setmenubutton → выбери бота → укажи URL Mini App
```

Или бот сам попытается установить кнопку меню при запуске.

## Локальное тестирование без Telegram

Можно просто открыть `http://localhost:8000` в браузере — API работает в dev-режиме без проверки подписи Telegram.

## Экономика (MVP)

| Параметр              | Значение          |
|-----------------------|-------------------|
| Стартовый капитал     | 1500 💰           |
| Энергия               | 100 (растёт с уровнем) |
| Реген энергии         | 1 ед. / 3 мин     |
| Работы                | 120–800 💰        |
| Имущество             | от 2500 💰        |
| Пассивный доход       | до 700/час        |

## Что можно добавить дальше

- Кланы / банды
- Криминал + полиция
- Фондовый рынок
- Аватары и кастомизация
- Ежедневные квесты
- PostgreSQL вместо SQLite
- Админ-панель

## Технологии

- **Bot**: aiogram 3
- **Backend**: FastAPI + SQLAlchemy 2 + aiosqlite
- **Frontend**: Vanilla JS + Telegram WebApp SDK
- **UI**: тёмная тема, неон, Inter

---

Сделано с 💜 для Telegram Mini Apps
