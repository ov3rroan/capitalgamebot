from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, BigInteger, Float, Boolean, DateTime, ForeignKey, Text
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.getenv("DB_PATH", "/tmp/capital_city.db")
DEFAULT_DB = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"

raw_url = os.getenv("DATABASE_URL", DEFAULT_DB)

# Railway/Render/Heroku дают postgresql:// — переводим на async-драйвер
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif raw_url.startswith("postgresql://") and "+asyncpg" not in raw_url:
    raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

DATABASE_URL = raw_url

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    balance: Mapped[float] = mapped_column(Float, default=1000.0)  # стартовый капитал
    energy: Mapped[int] = mapped_column(Integer, default=100)
    max_energy: Mapped[int] = mapped_column(Integer, default=100)
    level: Mapped[int] = mapped_column(Integer, default=1)
    exp: Mapped[int] = mapped_column(Integer, default=0)
    reputation: Mapped[int] = mapped_column(Integer, default=0)
    influence: Mapped[int] = mapped_column(Integer, default=0)

    last_energy_update: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_job_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    properties = relationship("UserProperty", back_populates="owner")
    job_skills = relationship("JobSkill", back_populates="user")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text)
    min_level: Mapped[int] = mapped_column(Integer, default=1)
    energy_cost: Mapped[int] = mapped_column(Integer, default=10)
    base_income: Mapped[float] = mapped_column(Float)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=60)
    risk: Mapped[float] = mapped_column(Float, default=0.0)  # шанс провала 0-1
    icon: Mapped[str] = mapped_column(String(16), default="💼")


class JobSkill(Base):
    __tablename__ = "job_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    level: Mapped[int] = mapped_column(Integer, default=1)
    exp: Mapped[int] = mapped_column(Integer, default=0)

    user = relationship("User", back_populates="job_skills")


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    type: Mapped[str] = mapped_column(String(32))  # housing, vehicle, business
    price: Mapped[float] = mapped_column(Float)
    income_per_hour: Mapped[float] = mapped_column(Float, default=0.0)
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String(16), default="🏠")
    min_level: Mapped[int] = mapped_column(Integer, default=1)


class UserProperty(Base):
    __tablename__ = "user_properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_collected: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="properties")
    property = relationship("Property")


class CasinoLog(Base):
    __tablename__ = "casino_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    game: Mapped[str] = mapped_column(String(32))
    bet: Mapped[float] = mapped_column(Float)
    win: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed data
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Job).limit(1))
        if not result.scalar_one_or_none():
            jobs = [
                Job(name="Курьер", description="Доставляй заказы по городу", min_level=1, energy_cost=8, base_income=120, cooldown_seconds=45, risk=0.05, icon="🛵"),
                Job(name="Таксист", description="Вози пассажиров", min_level=1, energy_cost=12, base_income=180, cooldown_seconds=60, risk=0.08, icon="🚕"),
                Job(name="Бармен", description="Работай в ночном клубе", min_level=2, energy_cost=15, base_income=250, cooldown_seconds=90, risk=0.1, icon="🍸"),
                Job(name="Программист", description="Пиши код на фрилансе", min_level=3, energy_cost=20, base_income=450, cooldown_seconds=120, risk=0.05, icon="💻"),
                Job(name="Охранник", description="Охраняй объекты", min_level=2, energy_cost=18, base_income=300, cooldown_seconds=100, risk=0.15, icon="🛡️"),
                Job(name="Шахтёр", description="Добывай руду в шахтах (рискованно)", min_level=4, energy_cost=30, base_income=800, cooldown_seconds=180, risk=0.25, icon="⛏️"),
                Job(name="Стример", description="Стримь и собирай донаты", min_level=5, energy_cost=25, base_income=600, cooldown_seconds=150, risk=0.1, icon="🎥"),
            ]
            session.add_all(jobs)

            properties = [
                Property(name="Комната в общаге", type="housing", price=2500, income_per_hour=5, description="Скромное жильё для старта", icon="🛏️", min_level=1),
                Property(name="Квартира-студия", type="housing", price=12000, income_per_hour=25, description="Уютная студия в центре", icon="🏢", min_level=2),
                Property(name="Пентхаус", type="housing", price=150000, income_per_hour=350, description="Элитный пентхаус с видом", icon="🏙️", min_level=8),
                Property(name="Старый хэтчбек", type="vehicle", price=8000, income_per_hour=0, description="Ездит, но скрипит", icon="🚗", min_level=1),
                Property(name="Спорткар", type="vehicle", price=85000, income_per_hour=0, description="Быстрый и стильный", icon="🏎️", min_level=6),
                Property(name="Автомойка", type="business", price=35000, income_per_hour=80, description="Небольшой бизнес", icon="🚿", min_level=4),
                Property(name="Кафе", type="business", price=95000, income_per_hour=220, description="Уютное кафе в районе", icon="☕", min_level=7),
                Property(name="Ночной клуб", type="business", price=320000, income_per_hour=700, description="Клуб с хорошей репутацией", icon="🎧", min_level=12),
                Property(name="Крипто-ферма", type="business", price=180000, income_per_hour=450, description="Майнинг в гараже", icon="⛏️", min_level=9),
            ]
            session.add_all(properties)
            await session.commit()
