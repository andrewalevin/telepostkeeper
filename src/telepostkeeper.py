import argparse
import pathlib
import sys
from datetime import date, datetime
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from dotenv import load_dotenv
import os
import yaml

ENV_NAME_BOT_TOKEN = 'TELEPOSTKEEPER_BOT_TOKEN'
ENV_NAME_STORE = 'TELEPOSTKEEPER_STORE_DIR'
ENV_NAME_CHANNELS = 'TELEPOSTKEEPER_CHANNELS_IDS_LIST'

load_dotenv()

token = os.getenv(ENV_NAME_BOT_TOKEN, '').strip()
if not token:
    print(f'🔴 No {ENV_NAME_BOT_TOKEN} variable set in env. Make add and restart bot.')
    sys.exit()

store = os.getenv("ENV_NAME_STORE")
if not store or store == ".":
    store = pathlib.Path(".")
else:
    store = pathlib.Path(store.strip())

store.mkdir(parents=True, exist_ok=True)

channels_list = [int(item) for item in os.getenv(ENV_NAME_CHANNELS, '').strip().split(',') if item.isdigit()]


bot = Bot(token=token)
dp = Dispatcher()

async def update_chat_index(sender, chat_dir: pathlib.Path):
    print('🦠 update_chat_index: ')
    full_name = sender.full_name

    last_full_name = ''
    about_yaml = chat_dir / f'about.yaml'

    if about_yaml.exists():
        try:
            with about_yaml.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            last_full_name = data.get("full_name", "")
        except yaml.YAMLError as e:
            print("Failed to load YAML from %s: %s", about_yaml, e)
        except Exception as e:
            print("Unexpected error reading %s: %s", about_yaml, e)

    if last_full_name != full_name:
        print('🧬 rename')
        try:
            data = {"full_name": full_name}
            with about_yaml.open("w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            print("Updated index.yaml with new full_name: %s", full_name)
        except yaml.YAMLError as e:
            print("Failed to write YAML to %s: %s", about_yaml, e)
        except Exception as e:
            print("Unexpected error writing %s: %s", about_yaml, e)


def get_real_chat_id(chat_id_raw):
    return -chat_id_raw - 1000000000000

@dp.channel_post()
async def handler_channel_post(message: Message):
    print('💈 handler_channel_post')

    real_chat_id = get_real_chat_id(message.sender_chat.id)
    if real_chat_id not in channels_list:
        return

    chat_dir = store / f'chat-{real_chat_id}'
    asyncio.create_task(update_chat_index(message.sender_chat, chat_dir))

    now = datetime.now()
    post_file = chat_dir / f'{now.year}' / f'{now.month:02}' / f'{message.message_id}.yaml'
    post_file.parent.mkdir(exist_ok=True, parents=True)

    data = {
        'date': message.date.__str__(),
        'type': 'text',
        'html_text': message.html_text,
    }

    with post_file.open('w') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


async def run_bot():
    print('Bot is running ... ')
    await dp.start_polling(bot, handle_signals=True, close_bot_session=True)


def main():
    asyncio.run(run_bot())


if __name__ == '__main__':
    main()