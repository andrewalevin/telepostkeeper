
import json
import pathlib
import pprint
import sys
from datetime import date, datetime
import asyncio

from dotenv import load_dotenv
import os
import yaml
from telegram import Update, Video, Document, Audio
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
    print('🦠 update_chat_index: ')

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

    context['file_size'] = thumbnail.file_size
    context['height'] = thumbnail.height
    context['width'] = thumbnail.width

    thumb_file = await thumbnail.get_file()
    thumb_path = pathlib.Path(thumb_file.file_path)
    thumb_store_path = root_path / f'{post_id}-thumbnail{thumb_path.suffix}'

    context['path'] = thumb_store_path.as_posix()
    print('THUMB CONTEXT: ', context)

    try:
        task_created = asyncio.create_task(thumb_file.download_to_drive(thumb_store_path))
    except Exception as e:
        print('Exception in Thumb')

        task_created = asyncio.create_task(empty_task())

    return context, task_created


def get_extension(file: Video | Audio | Document) -> str:
    ext = '.file'

    if hasattr(file, 'file_name'):
        if file.file_name:
            try:
                ext = pathlib.Path(file.file_name).suffix
            except Exception as e:
                ext = '.file'

    if hasattr(file, 'mime_type'):
        if file.mime_type:
            try:
                ext = file.mime_type.split('/')[-1]
                ext = f'.{ext}'
            except Exception as e:
                ext = '.file'

    return ext

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
    asyncio.create_task(update_chat_about_info(message.sender_chat.full_name, chat_dir))

    now = datetime.now()
    post_file = chat_dir / f'{now.year}' / f'{now.month:02}' / f'{message.message_id}.yaml'
    post_file.parent.mkdir(exist_ok=True, parents=True)

    context = dict()

    context['date'] = message.date
    context['type'] = ''

    if message.media_group_id:
        context['media_group_id'] = message.media_group_id

    if message.text:
        context['type'] = 'text'
        context['text'] = message.text_html

    if message.caption:
        context['caption'] = message.caption_html

    pending_task_heavy = asyncio.create_task(empty_task())
    pending_task_thumbnail = asyncio.create_task(empty_task())

    if message.photo:
        print('🖼 Photo: ')
        context['type'] = 'photo'

        photo = message.photo[-1]
        context['file_size'] = photo.file_size
        context['height'] = photo.height
        context['width'] = photo.width

        photo_file = await photo.get_file()
        audio_store_path = post_file.parent / f'{message.message_id}-photo{pathlib.Path(photo_file.file_path).suffix}'
        context['path'] = audio_store_path.as_posix()

        pending_task_heavy = asyncio.create_task(photo_file.download_to_drive(audio_store_path))

    if message.document:
        print('🗂 Document: ')
        context['type'] = 'document'

        document = message.document

        context['file_size'] = document.file_size
        context['file_name'] = document.file_name

        audio_store_path = post_file.parent / f'{message.message_id}-document{pathlib.Path(document.file_name).suffix}'
        context['path'] = audio_store_path.as_posix()

        audio_file = await document.get_file()

        pending_task_heavy = asyncio.create_task(audio_file.download_to_drive(audio_store_path))

        if document.thumbnail:
            _c_thumb, pending_task_thumbnail = await make_thumbnail(
                document.thumbnail, post_file.parent, message.message_id)

            context['thumbnail_file_size'] = _c_thumb['file_size']
            context['thumbnail_height'] = _c_thumb['height']
            context['thumbnail_width'] = _c_thumb['width']
            context['thumbnail_path'] =  _c_thumb['path']

    if message.audio:
        print('📣 Audio: ')

        audio = message.audio
        context['type'] = 'audio'
        context['file_size'] = audio.file_size
        context['file_name'] = audio.file_name
        if hasattr(audio, 'title'):
            context['title'] = audio.title
        context['duration'] = audio.duration

        audio_store_path = post_file.parent / f'{message.message_id}-audio{pathlib.Path(audio.file_name).suffix}'
        context['path'] = audio_store_path.as_posix()

        audio_file = await audio.get_file()

        pending_task_heavy = asyncio.create_task(
            audio_file.download_to_drive(audio_store_path))

        if audio.thumbnail:
            _c_thumb, pending_task_thumbnail = await make_thumbnail(audio.thumbnail, post_file.parent, message.message_id)

            context['thumbnail_file_size'] = _c_thumb['file_size']
            context['thumbnail_height'] = _c_thumb['height']
            context['thumbnail_width'] = _c_thumb['width']
            context['thumbnail_path'] =  _c_thumb['path']

    if message.video:
        print('📺 Video: ')

        video = message.video
        context['type'] = 'video'
        context['file_size'] = video.file_size
        context['file_name'] = video.file_name
        if hasattr(video, 'title'):
            context['title'] = video.title
        context['height'] = video.height
        context['height'] = video.width
        context['duration'] = video.duration

        video_store_path = post_file.parent / f'{message.message_id}-video{get_extension(video)}'
        context['path'] = video_store_path.as_posix()

        if video.thumbnail:
            _c_thumb, pending_task_thumbnail = await make_thumbnail(
                video.thumbnail, post_file.parent, message.message_id)

            context['thumbnail_file_size'] = _c_thumb['file_size']
            context['thumbnail_height'] = _c_thumb['height']
            context['thumbnail_width'] = _c_thumb['width']
            context['thumbnail_path'] =  _c_thumb['path']

        print('File Size: ', video.file_size)
        print(video.file_size.real)
        print(video.file_size.imag)
        print()

        # todo make chunk download


        try:
            video_file = await video.get_file()

            pending_task_heavy = asyncio.create_task(video_file.download_to_drive(video_store_path))

        except Exception as e:
            pass

    if message.voice:
        print('🎤 Voice: ')

        # todo

    # todo quote:

    # location

    with post_file.open('w') as f:
        yaml.dump(context, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    if pending_task_thumbnail:
        print('🛰 Task Thumbnail')
        await pending_task_thumbnail

    if pending_task_heavy:
        print('🛰 Task Heavy')
        await pending_task_heavy








def run_bot():
    print('Bot is running ... ')
    application = ApplicationBuilder().token(token).build()

    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handler_channel_post))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    run_bot()


if __name__ == '__main__':
    main()