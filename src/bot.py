import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message

from dotenv import load_dotenv

load_dotenv()

TELEPOSTKEEPER_BOT_TOKEN = os.getenv("TELEPOSTKEEPER_BOT_TOKEN")
if not TELEPOSTKEEPER_BOT_TOKEN:
    raise ValueError("TELEPOSTKEEPER_BOT_TOKEN is not set in the .env file")

bot = Bot(token=TELEPOSTKEEPER_BOT_TOKEN)
dp = Dispatcher()


@dp.message()
async def ping_pong(message: Message):
    print('🌎 Got Message: ', message.text)
    print()

    await message.reply("PONG")


async def run_bot():
    print("Bot is starting...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()