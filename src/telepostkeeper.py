
import pathlib
import pprint
import sys
from datetime import datetime
import asyncio
from typing import Optional

import aiohttp
from dotenv import load_dotenv
import os
import yaml
from telegram import Update, Video, Document, Audio, Message, Chat, PhotoSize
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

ENV_NAME_BOT_TOKEN = 'TELEPOSTKEEPER_BOT_TOKEN'
ENV_NAME_STORE = 'TELEPOSTKEEPER_STORE_DIR'
ENV_NAME_CHANNELS = 'TELEPOSTKEEPER_CHANNELS_IDS_LIST'
ENV_NAME_CHANNELS_ENCRYPTED = 'TELEPOSTKEEPER_CHANNELS_IDS_LIST_ENCRYPTED'
ENV_NAME_ENCRYPTION_PRIVATE_KEY = 'TELEPOSTKEEPER_ENCRYPTION_PRIVATE_KEY'

load_dotenv()

token = os.getenv(ENV_NAME_BOT_TOKEN, '').strip()
if not token:
    print(f'🔴 No {ENV_NAME_BOT_TOKEN} variable set in env. Make add and restart bot.')
    sys.exit()

store = os.getenv(ENV_NAME_STORE)
if not store or store == ".":
    store = pathlib.Path(".")
else:
    store = pathlib.Path(store.strip())
store.mkdir(parents=True, exist_ok=True)
print('🏈️ store: ', store)

channels_list = [int(item) for item in os.getenv(ENV_NAME_CHANNELS, '').strip().split(',') if item.isdigit()]
print('🏈️ channels_list: ', channels_list)

channels_list_encrypted = [int(item) for item in os.getenv(ENV_NAME_CHANNELS_ENCRYPTED, '').strip().split(',') if item.isdigit()]
print('🏈️ channels_list_encrypted: ', channels_list_encrypted)

encryption_private_key = ''
if private_key := os.getenv(ENV_NAME_ENCRYPTION_PRIVATE_KEY, '').strip():
    encryption_private_key = private_key
print('🏈️ encryption_private_key: ', encryption_private_key)


skip_download_media_types = []

MEDIA_TYPES_ALL = ['text', 'photo', 'document', 'audio', 'video', 'voice', 'location', 'sticker']

for media_type in MEDIA_TYPES_ALL:
    value = os.getenv(f'TELEPOSTKEEPER_SKIP_DOWNLOAD_{media_type.upper()}', '').lower()
    if value == 'true':
        skip_download_media_types.append(media_type)
print('🏈️ skip_download_media_types: ', skip_download_media_types)

skip_download_bigger = 987654321
if env_max_file_size := os.getenv(f'TELEPOSTKEEPER_SKIP_DOWNLOAD_BIGGER', ''):
    if env_max_file_size.isdigit():
        skip_download_bigger = max(10, min(int(env_max_file_size), skip_download_bigger))
print('🏈️ skip_download_bigger: ', skip_download_bigger)

skip_download_thumbnail = False
if env_skip_down_thumb := os.getenv(f'TELEPOSTKEEPER_SKIP_DOWNLOAD_THUMBNAIL', '').lower():
    if env_skip_down_thumb == 'true':
        skip_download_thumbnail = True
print('🏈️ skip_download_thumbnail: ', skip_download_thumbnail)

# todo Refactor




async def update_chat_about_info(chat: Chat, chat_dir: pathlib.Path):
    about_path = chat_dir / f'about.yaml'

    last_full_name = ''
    if about_path.exists():
        try:
            with about_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            last_full_name = data.get("full_name", "")
        except yaml.YAMLError as e:
            print("Failed to load YAML from %s: %s", about_path, e)
        except Exception as e:
            print("Unexpected error reading %s: %s", about_path, e)

    if last_full_name != chat.full_name:
        try:
            data = {"full_name": chat.full_name}
            with about_path.open("w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            print("Updated index.yaml with new full_name: %s", chat.full_name)
        except yaml.YAMLError as e:
            print("Failed to write YAML to %s: %s", about_path, e)
        except Exception as e:
            print("Unexpected error writing %s: %s", about_path, e)


def get_real_chat_id(chat_id_raw: int) -> int:
    return - chat_id_raw - 1000000000000


async def get_extension_media_heavy_object(media_type: str, media_obj: Video | Audio | Document | PhotoSize) -> str:
    if media_type == 'photo':
        return '.jpg'

    if hasattr(media_obj, 'file_name') and media_obj.file_name:
        try:
            ext = pathlib.Path(media_obj.file_name).suffix
        except Exception as e:
            print(f'🎸 Error {e}')
            ext = ''

        return ext

    if hasattr(media_obj, 'mime_type') and media_obj.mime_type:
            try:
                ext = media_obj.mime_type.split('/')[-1]
                ext = f'.{ext}'
            except Exception as e:
                print(f'🎸 Error {e}')
                ext = ''

            return ext

    try:
        _file = await media_obj.get_file()

        if hasattr(_file, 'file_path') and _file.file_path:
            try:
                _path = pathlib.Path(_file.file_path)
                ext = _path.suffix
            except Exception as e:
                print(f'Error {e}')
                ext = ''

            return ext

    except Exception as e:
        print(f'Error {e}')

    return ''


async def download_by_chunks_large(url: str, destination):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            with open(destination, 'wb') as f:
                # Download in chunks (e.g., 1MB per chunk)
                while True:
                    chunk = await response.content.read(64 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    f.write(chunk)


async def make_file_download(media_obj: any, path_media_obj: pathlib.Path):
    try:
        _file = await media_obj.get_file()
    except Exception as e:
        print(f"1-Error downloading file to {path_media_obj}: {e}")
        return

    if _file.file_size < 12000:
        try:
            await _file.download_to_drive(path_media_obj)
        except Exception as e:
            print(f"2-Error downloading file to {path_media_obj}: {e}")
            return
    else:
        try:
            await download_by_chunks_large(_file.file_path, path_media_obj)
        except Exception as e:
            print(f"3-Error downloading file to {path_media_obj}: {e}")
            return

    return path_media_obj

def identify_media_type(message: Message) -> Optional[str]:
    for media_type in MEDIA_TYPES_ALL:
        if hasattr(message, media_type):
            if getattr(message, media_type):
                return media_type
    return ''


async def handler_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post:
        return

    message = update.channel_post

    print('🍎', yaml.dump(message, default_flow_style=False))
    print()

    real_chat_id = get_real_chat_id(message.sender_chat.id)
    if real_chat_id not in channels_list:
        return

    chat_dir = store / f'chat-{real_chat_id}'
    pending_task_update_about = update_chat_about_info(message.sender_chat, chat_dir)

    now = datetime.now()
    post_dir = chat_dir / f'{now.year}' / f'{now.month:02}'
    post_dir.mkdir(exist_ok=True, parents=True)

    media_type: str = identify_media_type(message)
    if not media_type:
        return

    context = dict()

    context['date'] = message.date
    context['type'] = media_type

    pending_task_download_thumbnail = None
    pending_task_download_media_heavy = None

    if media_type == 'text':
        if message.text:
            context['text'] = message.text_html

    elif media_type == 'location':
        if message.location:
            context['latitude'] = message.location.latitude
            context['longitude'] = message.location.longitude

    elif media_type in ['photo', 'document', 'audio', 'video', 'voice', 'sticker']:
        if message.media_group_id:
            context['media_group_id'] = message.media_group_id

        if message.caption:
            context['caption'] = message.caption_html

        media_obj = getattr(message, media_type)

        if media_type == 'photo' and isinstance(media_obj, tuple):
            media_obj = media_obj[-1]

        for attr in ['file_name', 'file_size', 'title', 'height', 'width', 'duration']:
            if hasattr(media_obj, attr):
                context[attr] = getattr(media_obj, attr)

        if hasattr(media_obj, 'thumbnail'):
            if skip_download_thumbnail:
                context['thumbnail'] = 'skip'
            else:
                try:
                    thumb_file = await media_obj.thumbnail.get_file()
                    thumb_path = post_dir / f'{message.message_id}-thumbnail{pathlib.Path(thumb_file.file_path).suffix}'

                    pending_task_download_thumbnail = thumb_file.download_to_drive(thumb_path)

                    context['thumbnail_file_size'] = media_obj.thumbnail.file_size
                    context['thumbnail_height'] = media_obj.thumbnail.height
                    context['thumbnail_width'] = media_obj.thumbnail.width
                    context['thumbnail_path'] = thumb_path.as_posix()
                except Exception as e:
                    print('Error', e)

        if ext := await get_extension_media_heavy_object(media_type, media_obj):
            media_path = post_dir / f'{message.message_id}-{media_type}{ext}'
            context['path'] = media_path.as_posix()
            if media_obj.file_size > skip_download_bigger:
                print('Skipped Max File size')
                context['skip_download'] = f'max_file_size-{skip_download_bigger}'
            elif media_type in skip_download_media_types:
                print('Skipped Type')
                context['skip_download'] = f'file_type'
            else:
                pending_task_download_media_heavy = make_file_download(media_obj, media_path)

    if message.forward_origin:
        print()
        print('👺 FORAWARD: ')
        pprint.pprint(message.forward_origin)
        forward = message.forward_origin
        context['forward_date'] = forward.date

        sender = None
        if forward.type == forward.CHANNEL:
            context['forward_type'] = 'channel'
            sender = forward.chat

        elif forward.type == forward.USER:
            context['forward_type'] = 'user'
            sender = forward.sender_user

        else:
            context['forward_type'] = 'undefined'

        if sender:
            if hasattr(sender, 'id'):
               context['forward_chat_id'] = sender.id

            if hasattr(sender, 'title') and sender.title:
                context['forward_chat_title'] = sender.title

            if hasattr(sender, 'username') and sender.username:
                context['forward_chat_username'] = sender.username

            if hasattr(sender, 'first_name') and sender.first_name:
                context['forward_chat_first_name'] = sender.first_name

            if hasattr(sender, 'last_name') and sender.last_name:
                context['forward_chat_last_name'] = sender.last_name

    with post_dir.joinpath(f'{message.message_id}.yaml').open('w') as f:
        yaml.dump(context, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    if pending_task_download_thumbnail:
        await asyncio.create_task(pending_task_download_thumbnail)

    if pending_task_download_media_heavy:
        await asyncio.create_task(pending_task_download_media_heavy)

    if pending_task_update_about:
        await asyncio.create_task(pending_task_update_about)



def run_bot():
    print('Bot is running ... ')
    application = ApplicationBuilder().token(token).build()

    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handler_channel_post))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    run_bot()


if __name__ == '__main__':
    main()