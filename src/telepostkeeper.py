
import json
import pathlib
import pprint
import sys
from datetime import date, datetime
import asyncio

from aiogram.types import PhotoSize
from dotenv import load_dotenv
import os
import yaml
from telegram import Update, Video, Document, Audio, Message
from telegram._files._basethumbedmedium import _BaseThumbedMedium
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

ENV_NAME_BOT_TOKEN = 'TELEPOSTKEEPER_BOT_TOKEN'
ENV_NAME_STORE = 'TELEPOSTKEEPER_STORE_DIR'
ENV_NAME_CHANNELS = 'TELEPOSTKEEPER_CHANNELS_IDS_LIST'

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

channels_list = [int(item) for item in os.getenv(ENV_NAME_CHANNELS, '').strip().split(',') if item.isdigit()]



async def update_chat_about_info(full_name: str, chat_dir: pathlib.Path):
    print('🦠 update_chat_about: ')

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

async def empty_task():
    pass

async def make_thumbnail(thumbnail, root_path, post_id):
    context = dict()

    context['thumbnail_file_size'] = thumbnail.file_size
    context['thumbnail_height'] = thumbnail.height
    context['thumbnail_width'] = thumbnail.width

    thumb_file = await thumbnail.get_file()
    thumb_path = pathlib.Path(thumb_file.file_path)
    thumb_store_path = root_path / f'{post_id}-thumbnail{thumb_path.suffix}'

    context['thumbnail_path'] = thumb_store_path.as_posix()

    try:
        task_created = thumb_file.download_to_drive(thumb_store_path)
    except Exception as e:
        print('Exception in Thumb')
        task_created = empty_task()

    return context, task_created


def get_extension(media_obj: Video | Audio | Document | PhotoSize) -> str:
    ext = '.file'

    print('🔬 Extension')
    pprint.pprint(media_obj)
    print()
    print('media_obj.mime_type: ', media_obj.mime_type)
    print()

    if hasattr(media_obj, 'file_name'):
        if media_obj.file_name:
            try:
                ext = pathlib.Path(media_obj.file_name).suffix
            except Exception as e:
                print(f'🎸 Errro {e}')

    if ext != '.file':
        return ext

    if hasattr(media_obj, 'mime_type'):
        print('media_obj.mime_type: ', media_obj.mime_type)
        if media_obj.mime_type:
            try:
                ext = media_obj.mime_type.split('/')[-1]
                ext = f'.{ext}'
            except Exception as e:
                print(f'🎸 Errro {e}')

    return ext


async def make_file_download(media_obj_type: str, media_obj: any, file_path: pathlib.Path):
    print('Download: ')
    pprint.pprint(media_obj)
    print()

    if media_obj_type == 'photo':
        media_obj = media_obj[-1]
        print('Photo ')
        pprint.pprint(media_obj)

    if not hasattr(media_obj, 'get_file'):
        return

    try:
        _file = await media_obj.get_file()
        await _file.download_to_drive(file_path)
    except Exception as e:
        print(f'🍎 Error Doanloading: \t {e}')

    # todo make chunk download


def identify_media_type(message: Message):
    media_types = ['photo', 'document', 'audio', 'video', 'voice']
    for media_type in media_types:
        if hasattr(message, media_type):
            if getattr(message, media_type):
                return media_type
    return ''


async def handler_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post:
        return

    message = update.channel_post

    print('🍎 update_id: ', update.update_id)
    print('🍎', yaml.dump(message, default_flow_style=False))
    print()

    real_chat_id = get_real_chat_id(message.sender_chat.id)
    if real_chat_id not in channels_list:
        return

    chat_dir = store / f'chat-{real_chat_id}'
    task_about_update = update_chat_about_info(message.sender_chat.full_name, chat_dir)

    now = datetime.now()
    post_dir = chat_dir / f'{now.year}' / f'{now.month:02}'
    post_dir.mkdir(exist_ok=True, parents=True)

    pending_task_download_thumbnail = empty_task()
    pending_task_download_media_heavy = empty_task()

    context = dict()

    context['date'] = message.date
    context['type'] = 'text'
    if hasattr(message, 'text'):
        if message.text:
            context['text'] = message.text_html


    print('📺 Media Type: ')

    media_type: str = identify_media_type(message)
    if media_type:
        context['type'] = media_type
        if hasattr(message, 'media_group_id'):
            if getattr(message, 'media_group_id'):
                context['media_group_id'] = getattr(message, 'media_group_id')

        media_obj = getattr(message, media_type)

        attributes = [
            'file_size',
            'file_name',
            'title',
            'height',
            'width',
            'duration',
        ]
        for attr in attributes:
            if hasattr(media_obj, attr):
                context[attr] = getattr(media_obj, attr)

        ext = get_extension(media_obj) if media_type != 'photo' else'.jpg'
        print('EXT: ', ext)

        media_path = post_dir / f'{message.message_id}-{media_type}{ext}'
        context['path'] = media_path.as_posix()

        if hasattr(message, 'caption'):
            if message.caption:
                context['caption'] = message.caption_html

        if hasattr(media_obj, 'thumbnail'):
            thumb_cnt, pending_task_download_thumbnail = await make_thumbnail(
                media_obj.thumbnail, post_dir, message.message_id)
            context.update({key: thumb_cnt[key] for key in thumb_cnt})

        pending_task_download_media_heavy = make_file_download(
            media_type, media_obj, media_path)


    with post_dir.joinpath(f'{message.message_id}.yaml').open('w') as f:
        yaml.dump(context, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    if media_type:
        print('🛰 Task Thumbnail')
        await asyncio.create_task(pending_task_download_thumbnail)

        print('🛰 Task Heavy')
        await asyncio.create_task(pending_task_download_media_heavy)

    print('🛰 Task About Update')
    await asyncio.create_task(task_about_update)



def run_bot():
    print('Bot is running ... ')
    application = ApplicationBuilder().token(token).build()

    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handler_channel_post))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    run_bot()


if __name__ == '__main__':
    main()