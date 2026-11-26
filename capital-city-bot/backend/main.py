from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, timedelta
from pydantic import BaseModel
import random
import os
import hashlib
import hmac
import json
from urllib.parse import parse_qsl
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env из корня проекта
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from database import async_session, init_db, User, Job, Property, UserProperty, JobSkill, CasinoLog

app = FastAPI(title="Город Капитала API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")


async def get_db():
    async with async_session() as session:
        yield session


def validate_telegram_data(init_data: str) -> dict | None:
    """Проверка данных от Telegram WebApp"""
    if not BOT_TOKEN or not init_data:
        # В режиме разработки разрешаем без токена
        if not BOT_TOKEN:
            try:
                parsed = dict(parse_qsl(init_data))
                user = json.loads(parsed.get("user", "{}"))
                return user
            except Exception:
                return None
        return None

    try:
        parsed = dict(parse_qsl(init_data))
        check_hash = parsed.pop("hash", None)
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if calculated != check_hash:
            return None

        user = json.loads(parsed.get("user", "{}"))
        return user
    except Exception:
        return None


async def get_or_create_user(telegram_user: dict, db: AsyncSession) -> User:
    telegram_id = telegram_user.get("id")
    if not telegram_id:
        raise HTTPException(400, "No telegram id")

    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=telegram_id,
            username=telegram_user.get("username"),
            first_name=telegram_user.get("first_name"),
            last_name=telegram_user.get("last_name"),
            balance=1500.0,
            energy=100,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # обновляем имя на всякий случай
        user.username = telegram_user.get("username")
        user.first_name = telegram_user.get("first_name")
        await db.commit()

    # Регенерация энергии (1 энергия каждые 3 минуты)
    now = datetime.utcnow()
    if user.last_energy_update:
        minutes_passed = (now - user.last_energy_update).total_seconds() / 60
        energy_to_add = int(minutes_passed // 3)
        if energy_to_add > 0:
            user.energy = min(user.max_energy, user.energy + energy_to_add)
            user.last_energy_update = now
            await db.commit()

    return user


# ============ Schemas ============

class AuthRequest(BaseModel):
    initData: str


class WorkRequest(BaseModel):
    initData: str
    job_id: int


class BuyPropertyRequest(BaseModel):
    initData: str
    property_id: int


class CasinoRequest(BaseModel):
    initData: str
    game: str  # slots / roulette / dice
    bet: float


# ============ Routes ============

@app.on_event("startup")
async def startup():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)
    await init_db()


@app.post("/api/auth")
async def auth(data: AuthRequest, db: AsyncSession = Depends(get_db)):
    tg_user = validate_telegram_data(data.initData)
    if not tg_user:
        # fallback для локальной разработки
        tg_user = {"id": 123456789, "first_name": "Тестер", "username": "tester"}

    user = await get_or_create_user(tg_user, db)

    # Считаем стоимость имущества
    result = await db.execute(
        select(func.coalesce(func.sum(Property.price), 0))
        .select_from(UserProperty)
        .join(Property)
        .where(UserProperty.user_id == user.id)
    )
    property_value = result.scalar() or 0

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "name": user.first_name or user.username or "Игрок",
        "username": user.username,
        "balance": round(user.balance, 2),
        "energy": user.energy,
        "max_energy": user.max_energy,
        "level": user.level,
        "exp": user.exp,
        "reputation": user.reputation,
        "influence": user.influence,
        "property_value": property_value,
    }


@app.get("/api/jobs")
async def get_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).order_by(Job.min_level))
    jobs = result.scalars().all()
    return [
        {
            "id": j.id,
            "name": j.name,
            "description": j.description,
            "min_level": j.min_level,
            "energy_cost": j.energy_cost,
            "base_income": j.base_income,
            "cooldown_seconds": j.cooldown_seconds,
            "risk": j.risk,
            "icon": j.icon,
        }
        for j in jobs
    ]


@app.post("/api/work")
async def do_work(data: WorkRequest, db: AsyncSession = Depends(get_db)):
    tg_user = validate_telegram_data(data.initData)
    if not tg_user:
        tg_user = {"id": 123456789, "first_name": "Тестер"}

    user = await get_or_create_user(tg_user, db)

    result = await db.execute(select(Job).where(Job.id == data.job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Работа не найдена")

    if user.level < job.min_level:
        raise HTTPException(400, f"Нужен {job.min_level} уровень")

    if user.energy < job.energy_cost:
        raise HTTPException(400, "Недостаточно энергии")

    # Проверка кулдауна (упрощённо — общий last_job_time)
    if user.last_job_time:
        elapsed = (datetime.utcnow() - user.last_job_time).total_seconds()
        if elapsed < 20:  # минимальный кулдаун между любыми работами
            raise HTTPException(400, f"Подожди ещё {int(20 - elapsed)} сек")

    # Шанс провала
    if random.random() < job.risk:
        user.energy -= job.energy_cost // 2
        user.last_job_time = datetime.utcnow()
        await db.commit()
        return {
            "success": False,
            "message": f"Неудача! Ты потратил {job.energy_cost // 2} энергии и ничего не заработал.",
            "balance": user.balance,
            "energy": user.energy,
        }

    # Успех
    skill_result = await db.execute(
        select(JobSkill).where(JobSkill.user_id == user.id, JobSkill.job_id == job.id)
    )
    skill = skill_result.scalar_one_or_none()
    if not skill:
        skill = JobSkill(user_id=user.id, job_id=job.id, level=1)
        db.add(skill)

    income = job.base_income * (1 + (skill.level - 1) * 0.08)
    income = round(income * random.uniform(0.9, 1.15), 2)

    user.balance += income
    user.energy -= job.energy_cost
    user.exp += 8 + job.min_level * 2
    user.last_job_time = datetime.utcnow()

    # Прокачка навыка
    skill.exp += 12
    if skill.exp >= skill.level * 50:
        skill.level += 1
        skill.exp = 0

    # Уровень игрока
    while user.exp >= user.level * 100:
        user.exp -= user.level * 100
        user.level += 1
        user.max_energy = 100 + (user.level - 1) * 5
        user.influence += 2

    await db.commit()

    return {
        "success": True,
        "message": f"Ты заработал {income} 💰 на работе «{job.name}»!",
        "income": income,
        "balance": round(user.balance, 2),
        "energy": user.energy,
        "level": user.level,
        "exp": user.exp,
        "skill_level": skill.level,
    }


@app.get("/api/properties")
async def get_properties(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Property).order_by(Property.price))
    props = result.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "type": p.type,
            "price": p.price,
            "income_per_hour": p.income_per_hour,
            "description": p.description,
            "icon": p.icon,
            "min_level": p.min_level,
        }
        for p in props
    ]


@app.post("/api/buy_property")
async def buy_property(data: BuyPropertyRequest, db: AsyncSession = Depends(get_db)):
    tg_user = validate_telegram_data(data.initData)
    if not tg_user:
        tg_user = {"id": 123456789, "first_name": "Тестер"}

    user = await get_or_create_user(tg_user, db)

    result = await db.execute(select(Property).where(Property.id == data.property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(404, "Имущество не найдено")

    if user.level < prop.min_level:
        raise HTTPException(400, f"Нужен {prop.min_level} уровень")

    if user.balance < prop.price:
        raise HTTPException(400, "Недостаточно денег")

    # Проверяем, не куплено ли уже
    existing = await db.execute(
        select(UserProperty).where(
            UserProperty.user_id == user.id,
            UserProperty.property_id == prop.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "У тебя уже есть это имущество")

    user.balance -= prop.price
    user.influence += int(prop.price / 5000)
    up = UserProperty(user_id=user.id, property_id=prop.id)
    db.add(up)
    await db.commit()

    return {
        "success": True,
        "message": f"Поздравляем! Ты купил «{prop.name}»",
        "balance": round(user.balance, 2),
        "influence": user.influence,
    }


@app.get("/api/my_properties")
async def my_properties(initData: str, db: AsyncSession = Depends(get_db)):
    tg_user = validate_telegram_data(initData)
    if not tg_user:
        tg_user = {"id": 123456789}

    user = await get_or_create_user(tg_user, db)

    result = await db.execute(
        select(UserProperty, Property)
        .join(Property)
        .where(UserProperty.user_id == user.id)
    )
    items = result.all()

    now = datetime.utcnow()
    response = []
    total_pending = 0.0

    for up, prop in items:
        hours = (now - up.last_collected).total_seconds() / 3600
        pending = round(prop.income_per_hour * hours, 2)
        total_pending += pending
        response.append({
            "id": up.id,
            "property_id": prop.id,
            "name": prop.name,
            "type": prop.type,
            "icon": prop.icon,
            "income_per_hour": prop.income_per_hour,
            "pending_income": pending,
            "purchased_at": up.purchased_at.isoformat(),
        })

    return {"properties": response, "total_pending": round(total_pending, 2)}


@app.post("/api/collect_income")
async def collect_income(data: AuthRequest, db: AsyncSession = Depends(get_db)):
    tg_user = validate_telegram_data(data.initData)
    if not tg_user:
        tg_user = {"id": 123456789}

    user = await get_or_create_user(tg_user, db)

    result = await db.execute(
        select(UserProperty, Property)
        .join(Property)
        .where(UserProperty.user_id == user.id)
    )
    items = result.all()

    total = 0.0
    now = datetime.utcnow()
    for up, prop in items:
        hours = (now - up.last_collected).total_seconds() / 3600
        income = prop.income_per_hour * hours
        total += income
        up.last_collected = now

    total = round(total, 2)
    user.balance += total
    await db.commit()

    return {
        "success": True,
        "collected": total,
        "balance": round(user.balance, 2),
        "message": f"Собрано {total} 💰 с имущества",
    }


@app.post("/api/casino")
async def play_casino(data: CasinoRequest, db: AsyncSession = Depends(get_db)):
    tg_user = validate_telegram_data(data.initData)
    if not tg_user:
        tg_user = {"id": 123456789}

    user = await get_or_create_user(tg_user, db)

    if data.bet < 10:
        raise HTTPException(400, "Минимальная ставка 10")
    if data.bet > user.balance:
        raise HTTPException(400, "Недостаточно денег")
    if data.bet > 50000:
        raise HTTPException(400, "Максимальная ставка 50 000")

    user.balance -= data.bet
    win = 0.0
    result_text = ""

    if data.game == "slots":
        reels = [random.choice(["🍒", "🍋", "🔔", "💎", "7️⃣", "⭐"]) for _ in range(3)]
        if reels[0] == reels[1] == reels[2]:
            if reels[0] == "7️⃣":
                win = data.bet * 25
            elif reels[0] == "💎":
                win = data.bet * 12
            else:
                win = data.bet * 6
            result_text = f"{''.join(reels)} — ДЖЕКПОТ!"
        elif reels[0] == reels[1] or reels[1] == reels[2]:
            win = data.bet * 1.8
            result_text = f"{''.join(reels)} — Две совпали!"
        else:
            result_text = f"{''.join(reels)} — Пусто"

    elif data.game == "roulette":
        number = random.randint(0, 36)
        color = "green" if number == 0 else ("red" if number % 2 else "black")
        # Игрок всегда ставит на красное для простоты MVP
        if color == "red":
            win = data.bet * 2
            result_text = f"Выпало {number} 🔴 — Победа!"
        else:
            result_text = f"Выпало {number} {'🟢' if number == 0 else '⚫'} — Проигрыш"

    elif data.game == "dice":
        player = random.randint(1, 6) + random.randint(1, 6)
        dealer = random.randint(1, 6) + random.randint(1, 6)
        if player > dealer:
            win = data.bet * 2.1
            result_text = f"Ты: {player} vs Дилер: {dealer} — Победа!"
        elif player == dealer:
            win = data.bet  # возврат
            result_text = f"Ты: {player} vs Дилер: {dealer} — Ничья"
        else:
            result_text = f"Ты: {player} vs Дилер: {dealer} — Проигрыш"
    else:
        raise HTTPException(400, "Неизвестная игра")

    user.balance += win
    user.balance = round(user.balance, 2)

    log = CasinoLog(user_id=user.id, game=data.game, bet=data.bet, win=win)
    db.add(log)
    await db.commit()

    return {
        "success": True,
        "result": result_text,
        "win": win,
        "profit": round(win - data.bet, 2),
        "balance": user.balance,
    }


@app.get("/api/top")
async def get_top(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .order_by(desc(User.balance))
        .limit(limit)
    )
    users = result.scalars().all()

    return [
        {
            "place": i + 1,
            "name": u.first_name or u.username or f"Игрок {u.telegram_id}",
            "username": u.username,
            "balance": round(u.balance, 2),
            "level": u.level,
            "influence": u.influence,
        }
        for i, u in enumerate(users)
    ]


@app.get("/api/profile")
async def profile(initData: str, db: AsyncSession = Depends(get_db)):
    tg_user = validate_telegram_data(initData)
    if not tg_user:
        tg_user = {"id": 123456789, "first_name": "Тестер"}

    user = await get_or_create_user(tg_user, db)
    return {
        "name": user.first_name or user.username or "Игрок",
        "balance": round(user.balance, 2),
        "energy": user.energy,
        "max_energy": user.max_energy,
        "level": user.level,
        "exp": user.exp,
        "exp_next": user.level * 100,
        "reputation": user.reputation,
        "influence": user.influence,
    }


# Раздача Mini App
MINIAPP_DIR = os.path.join(os.path.dirname(__file__), "..", "miniapp")

@app.get("/")
async def index():
    return FileResponse(os.path.join(MINIAPP_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=MINIAPP_DIR), name="static")
