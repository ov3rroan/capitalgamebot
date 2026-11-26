import asyncio
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, MenuButtonWebApp
from aiogram.enums import ParseMode
from dotenv import load_dotenv

# Подхватываем .env из разных мест (локально / Docker)
for p in (Path("/app/.env"), Path(__file__).resolve().parent.parent / ".env", Path(".env")):
    if p.exists():
        load_dotenv(p, override=False)

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
WEBAPP_URL = (os.getenv("WEBAPP_URL") or "").strip()

# Если забыли https:// — добавляем
if WEBAPP_URL and not WEBAPP_URL.startswith("http"):
    WEBAPP_URL = "https://" + WEBAPP_URL
if WEBAPP_URL.endswith("/"):
    WEBAPP_URL = WEBAPP_URL[:-1]

print(f"[bot] BOT_TOKEN set: {'yes' if BOT_TOKEN else 'NO'}")
print(f"[bot] WEBAPP_URL: {WEBAPP_URL or 'NOT SET'}")

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN не найден. "
        "В Railway → Variables добавь BOT_TOKEN = токен от BotFather"
    )

if not WEBAPP_URL:
    print("[bot] WARNING: WEBAPP_URL пустой — кнопки Mini App не будут работать")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def main_keyboard():
    buttons = []
    if WEBAPP_URL:
        buttons.append([
            InlineKeyboardButton(
                text="🏙 Открыть Город Капитала",
                web_app=WebAppInfo(url=WEBAPP_URL),
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="📊 Топ игроков", callback_data="top"),
        InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    text = (
        "🏙 <b>Добро пожаловать в Город Капитала!</b>\n\n"
        "Это RP-симулятор жизни, где ты можешь:\n"
        "• 💼 Работать на разных работах\n"
        "• 🏠 Покупать имущество и получать пассивный доход\n"
        "• 🎰 Играть в казино\n"
        "• 🏆 Подниматься в топе по капиталу\n"
        "• 📈 Развивать влияние и уровень\n\n"
        "Нажми кнопку ниже, чтобы войти в город 👇"
    )
    await message.answer(text, reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)


@dp.message(Command("play"))
@dp.message(Command("app"))
async def cmd_play(message: types.Message):
    if not WEBAPP_URL:
        await message.answer("WEBAPP_URL не настроен. Укажи его в Variables на Railway.")
        return
    await message.answer(
        "🏙 Открываю Город Капитала...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Войти в игру", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]),
    )


@dp.callback_query(F.data == "help")
async def help_callback(callback: types.CallbackQuery):
    text = (
        "📖 <b>Как играть</b>\n\n"
        "1. Открой Mini App кнопкой «Открыть Город Капитала»\n"
        "2. Выполняй работы, чтобы зарабатывать деньги и опыт\n"
        "3. Покупай имущество — оно даёт пассивный доход\n"
        "4. Испытай удачу в казино «Неон»\n"
        "5. Соревнуйся в топе богатейших игроков\n\n"
        "Энергия восстанавливается автоматически (1 ед. каждые 3 минуты)."
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML)
    await callback.answer()


@dp.callback_query(F.data == "top")
async def top_callback(callback: types.CallbackQuery):
    kb = None
    if WEBAPP_URL:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏙 Открыть игру", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
    await callback.message.answer(
        "🏆 Топ игроков доступен внутри Mini App.\nОткрой игру и перейди во вкладку «Топ».",
        reply_markup=kb,
    )
    await callback.answer()


async def set_menu_button():
    if not WEBAPP_URL:
        return
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🏙 Город",
                web_app=WebAppInfo(url=WEBAPP_URL),
            )
        )
        print(f"[bot] Menu button set to {WEBAPP_URL}")
    except Exception as e:
        print(f"[bot] Не удалось установить menu button: {e}")


async def main():
    print("[bot] Бот запускается...")
    await set_menu_button()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
