import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, MenuButtonWebApp
from aiogram.enums import ParseMode
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com")  # Замени на свой URL Mini App

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не указан в .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🏙 Открыть Город Капитала",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )],
        [
            InlineKeyboardButton(text="📊 Топ игроков", callback_data="top"),
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
        ]
    ])


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
async def cmd_play(message: types.Message):
    await message.answer(
        "🏙 Открываю Город Капитала...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Войти в игру", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
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
        "Энергия восстанавливается автоматически (1 ед. каждые 3 минуты).\n"
        "Чем выше уровень работы — тем больше доход."
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML)
    await callback.answer()


@dp.callback_query(F.data == "top")
async def top_callback(callback: types.CallbackQuery):
    await callback.message.answer(
        "🏆 Топ игроков доступен внутри Mini App.\n"
        "Открой игру и перейди во вкладку «Топ».",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏙 Открыть игру", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
    )
    await callback.answer()


@dp.message(Command("app"))
async def cmd_app(message: types.Message):
    await message.answer(
        "Нажми кнопку, чтобы открыть игру:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏙 Город Капитала", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
    )


async def set_menu_button():
    """Устанавливает кнопку меню WebApp"""
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🏙 Город",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        )
    except Exception as e:
        print(f"Не удалось установить menu button: {e}")


async def main():
    print("Бот запускается...")
    await set_menu_button()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
