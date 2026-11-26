# Деплой «Город Капитала» на Railway (постоянный хостинг)

## Что получится
- Постоянный HTTPS-адрес для Mini App
- PostgreSQL (данные не пропадут)
- Бот и игра работают 24/7

---

## Шаг 1. Аккаунт Railway

1. Зайди на [https://railway.app](https://railway.app)
2. Войди через GitHub (рекомендуется)

---

## Шаг 2. Загрузи код на GitHub

1. Создай **новый репозиторий** на GitHub (можно приватный)
2. Залей туда папку `capital-city-bot`  
   (файл `.env` **не** должен попасть в репозиторий — он уже в `.dockerignore` и лучше добавить в `.gitignore`)

Если не хочешь GitHub — в Railway можно задеплоить через CLI (см. внизу).

---

## Шаг 3. Новый проект в Railway

1. **New Project** → **Deploy from GitHub repo**
2. Выбери репозиторий с ботом
3. Railway сам найдёт Dockerfile и начнёт сборку

---

## Шаг 4. Добавь базу данных

1. В проекте нажми **+ New** → **Database** → **PostgreSQL**
2. После создания зайди в Postgres → вкладка **Variables**
3. Скопируй значение `DATABASE_URL` (или просто нажми «Add Reference» к сервису приложения)

---

## Шаг 5. Переменные окружения

Открой свой сервис (web) → **Variables** → добавь:

| Переменная     | Значение                                      |
|----------------|-----------------------------------------------|
| `BOT_TOKEN`    | `8941491829:AAGFQrZzYwcvY6eXhXkqGq06Adm8t3CZoYk` |
| `WEBAPP_URL`   | пока оставь пустым или `https://placeholder`  |
| `DATABASE_URL` | (подтянется из Postgres автоматически)       |

После первого деплоя Railway даст тебе домен вида:
`https://xxx.up.railway.app`

Скопируй его и **поставь в `WEBAPP_URL`** → Redeploy.

---

## Шаг 6. Домен и кнопка бота

1. В Railway → Settings → Networking → **Generate Domain**
2. Скопируй получившийся URL (например `https://capital-city-production.up.railway.app`)
3. Вставь его в переменную `WEBAPP_URL`
4. Нажми **Redeploy**

После этого бот автоматически подхватит новый адрес Mini App.

Дополнительно можно вручную обновить кнопку меню:

```bash
curl -X POST "https://api.telegram.org/bot<ТОКЕН>/setChatMenuButton" \
  -H "Content-Type: application/json" \
  -d '{"menu_button":{"type":"web_app","text":"🏙 Город","web_app":{"url":"https://ТВОЙ-ДОМЕН.up.railway.app"}}}'
```

---

## Шаг 7. Проверка

1. Открой [@playcapitalgamebot](https://t.me/playcapitalgamebot)
2. /start → кнопка «Открыть Город Капитала»
3. Должна открыться игра

---

## Альтернатива без GitHub (Railway CLI)

На своём компьютере:

```bash
npm i -g @railway/cli
railway login
cd capital-city-bot
railway init
railway add --database postgres
railway variables set BOT_TOKEN=твой_токен
railway up
```

После деплоя:
```bash
railway domain
railway variables set WEBAPP_URL=https://полученный-домен.up.railway.app
railway up
```

---

## Важно про токен

Токен сейчас известен этой среде. После успешного деплоя **рекомендуется**:
1. Зайти к @BotFather → /revoke → получить новый токен
2. Обновить `BOT_TOKEN` в Railway
3. Старый токен перестанет работать

---

Если на каком-то шаге застрянешь — напиши, на каком именно, помогу.
