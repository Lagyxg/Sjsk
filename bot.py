import asyncio
import logging
import os
from html import escape

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, User

# --- НАСТРОЙКИ ---
TOKEN = os.getenv("BOT_TOKEN", "8510924588:AAFg1reHmaG2NAmRmAmYYOlUM-TSV1tjDV8")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1288679956"))  # куда приходят сообщения (твой ID или ID чата)

BUTTONS = ["Сотрудничество", "Фото/видео", "Переходник", "ТГК"]

PROMPTS = {
    "Сотрудничество": "Опиши, что хочешь предложить в качестве сотрудничестве",
    "Фото/видео": "Отправь своё фото или видео хохлов",
    "Переходник": "https://t.me/mertvihohol",
    "ТГК": "Актуальная ссылка на Телеграм канал: https://t.me/+iPzgzEt6z9IyZjFi ",
}

ALBUM_WAIT = 1.5  # сколько секунд ждём остальные файлы альбома

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Сотрудничество"), KeyboardButton(text="Фото/видео")],
        [KeyboardButton(text="Переходник"), KeyboardButton(text="ТГК")],
    ],
    resize_keyboard=True,
)

dp = Dispatcher()
dp.message.filter(F.chat.type == "private")  # работаем только в личке с ботом

user_category: dict[int, str] = {}
albums: dict[str, list[Message]] = {}


async def deliver(bot: Bot, user: User, chat_id: int, message_ids: list[int]) -> bool:
    """Шлёт админу одну шапку и сами сообщения. Возвращает True при успехе."""
    category = user_category.get(user.id, "Без категории")

    if user.username:
        contact = f"@{escape(user.username)}"
    else:
        contact = f'<a href="tg://user?id={user.id}">{escape(user.full_name)}</a> (юзернейма нет)'

    header = (
        f"📩 <b>{escape(category)}</b>\n"
        f"От: {escape(user.full_name)}\n"
        f"Аккаунт: {contact}\n"
        f"ID: <code>{user.id}</code>"
    )

    try:
        await bot.send_message(ADMIN_ID, header, parse_mode=ParseMode.HTML)
        await bot.copy_messages(ADMIN_ID, chat_id, message_ids)
        return True
    except TelegramAPIError:
        logging.exception("Не удалось отправить сообщение админу")
        return False


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Здарова, это бот-предложка канала Дохлые хрюшки. Тут ты можешь предложить свои фото/видео, предложить сотрудничество, а так же найти актуальные ссылки на переходник и на наш телеграм канал.", reply_markup=keyboard
    )


@dp.message(F.text.in_(BUTTONS))
async def choose_category(message: Message):
    user_category[message.from_user.id] = message.text
    await message.answer(PROMPTS[message.text], reply_markup=keyboard)


@dp.message(F.media_group_id)
async def album_part(message: Message, bot: Bot):
    gid = message.media_group_id
    if gid in albums:  # не первый файл альбома — просто добавляем в пачку
        albums[gid].append(message)
        return

    albums[gid] = [message]
    await asyncio.sleep(ALBUM_WAIT)  # ждём остальные файлы
    parts = sorted(albums.pop(gid), key=lambda m: m.message_id)

    ok = await deliver(bot, message.from_user, message.chat.id, [m.message_id for m in parts])
    await message.answer(
        "Отправлено ✅" if ok else "Не получилось отправить, попробуй позже.",
        reply_markup=keyboard,
    )


@dp.message()
async def single_message(message: Message, bot: Bot):
    ok = await deliver(bot, message.from_user, message.chat.id, [message.message_id])
    await message.answer(
        "Отправлено ✅" if ok else "Не получилось отправить, попробуй позже.",
        reply_markup=keyboard,
    )


async def main():
    logging.basicConfig(level=logging.INFO)
    if not ADMIN_ID or TOKEN.startswith("ВСТАВЬ"):
        raise SystemExit("Укажи BOT_TOKEN и ADMIN_ID (в файле или переменных окружения).")
    bot = Bot(TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
