import asyncio

import executor
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatMemberUpdated

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the token from the environment
bot_token = os.getenv("TELEPOSTKEEPER_BOT_TOKEN")

if bot_token:
    print("Bot token loaded successfully!")
else:
    print("Bot token not found!")

bot = Bot(token=bot_token)
dp = Dispatcher()

@dp.message_handler(commands=['promote_bot'])
async def promote_bot_command(message: types.Message):
    # Log the ID of the admin promoting the bot
    user_id = message.from_user.id
    username = message.from_user.username
    chat_id = message.chat.id
    await message.reply(f"Thanks for promoting me! User ID: {user_id}, Username: @{username}")
    # Log or store this data for further use
    print(f"Promoted by User ID: {user_id}, Username: @{username} in Chat ID: {chat_id}")


async def run_bot():
    print('Start: ')
    await dp.start_polling(bot)


def main():
    asyncio.run(run_bot())


if __name__ == '__main__':
    main()