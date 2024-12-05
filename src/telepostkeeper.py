import argparse
import inspect
import pathlib
import signal
import sys
from datetime import date, datetime
from pathlib import Path
import os

import asyncio

import executor
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatMemberUpdated, Message

from dotenv import load_dotenv
import os
import yaml

ENV_NAME_BOT_TOKEN = 'TELEPOSTKEEPER_BOT_TOKEN'
ENV_NAME_STORE = 'TELEPOSTKEEPER_STORE_DIR'
ENV_NAME_CHANNELS = 'TELEPOSTKEEPER_CHANNELS_IDS_LIST'

load_dotenv()

store = os.getenv(ENV_NAME_STORE, 'store')
store = pathlib.Path(store)
store.mkdir(parents=True, exist_ok=True)
print(store)


# Get the token from the environment
bot_token = os.getenv(ENV_NAME_BOT_TOKEN)

bot = Bot(token=bot_token)
dp = Dispatcher()

channels_list = [
    int(item)
    for item in os.getenv(ENV_NAME_CHANNELS, "").strip().split(',')
    if item.isdigit()
]
print('🍡 channels_listL: ', channels_list)



@dp.channel_post()
async def handler_channel_post(message: Message):
    print('💈 handler_channel_post')

    if -message.sender_chat.id - 1000000000000 not in channels_list:
        return

    now = datetime.now()
    post_file = store / f'{now.year}' / f'{now.month:02}' / f'{message.message_id}.yaml'
    post_file.parent.mkdir(exist_ok=True, parents=True)

    data = {
        'date': message.date.__str__(),
        'type': 'text',
        'html_text': message.html_text,
    }

    with post_file.open('w') as f:
        f.write(yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True))


async def run_bot():
    try:
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        print("🪭 Сигнал завершения получен.")
    finally:
        print("🪭 Звершение.")
        await dp.storage.close()
        await bot.session.close()
        print("🪭 Бот успешно завершил работу.")
        return


def handle_interrupt_or_suspend(signal, frame):
    print('handle_interrupt_or_suspend ')

    """Handle the SIGINT signal (Ctrl+C)."""
    print("Process interrupted by user. Exiting...")

    asyncio.get_event_loop().stop()
    sys.exit(0)


def main():
    signal.signal(signal.SIGTSTP, handle_interrupt_or_suspend)
    signal.signal(signal.SIGINT, handle_interrupt_or_suspend)

    print("Starting ... Press Ctrl+C to stop or Ctrl+Z to suspend.")

    parser = argparse.ArgumentParser(
        description='🥭 Bot', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    if not os.getenv(ENV_NAME_BOT_TOKEN, ''):
        print('🔴 No TG_TOKEN variable set in env. Make add and restart bot.')
        return

    print()
    asyncio.run(run_bot())
    print('END')


if __name__ == '__main__':
    main()