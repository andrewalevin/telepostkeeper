import logging
import pathlib
import sys
from typing import Optional

from dotenv import load_dotenv
import os
from telegram import Update, Video, Document, Audio, Message, Chat, PhotoSize
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from telepostkeeper.encryption import encrypt_aes, encrypt_aes_file
from telepostkeeper.utils import read_yaml, write_yaml, get_md5

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Environment variable names
ENV_NAME_BOT_TOKEN = 'TPK_BOT_TOKEN'
ENV_NAME_STORE = 'TPK_STORE_DIR'
ENV_NAME_CHANNELS = 'TPK_CHANNELS_IDS_LIST'
ENV_NAME_CHANNELS_ENCRYPTED = 'TPK_CHANNELS_IDS_LIST_ENCRYPTED'
ENV_NAME_ENCRYPTION_PRIVATE_KEY = 'TPK_ENCRYPTION_PRIVATE_KEY'

load_dotenv()

# Load configurations from environment variables
token = os.getenv(ENV_NAME_BOT_TOKEN, '').strip()
if not token:
    logger.error(f"No {ENV_NAME_BOT_TOKEN} variable set in env. Please add and restart the bot.")
    sys.exit()

store = os.getenv(ENV_NAME_STORE, "..").strip()
store_path = pathlib.Path(store)
store_path.mkdir(parents=True, exist_ok=True)
logger.info(f"🔹 Store directory set to: {store_path}")

channels_list = [
    int(item) for item in os.getenv(ENV_NAME_CHANNELS, '').strip().split(',') if item.isdigit()
]
logger.info(f"🔹 Channels list: {channels_list}")

channels_list_encrypted = [
    int(item) for item in os.getenv(ENV_NAME_CHANNELS_ENCRYPTED, '').strip().split(',') if item.isdigit()
]
logger.info(f"🔹 Encrypted channels list: {channels_list_encrypted}")


# Media type settings
skip_download_media_types = []
MEDIA_TYPES_ALL = ['text', 'photo', 'document', 'audio', 'video', 'voice', 'location', 'sticker']

for media_type in MEDIA_TYPES_ALL:
    value = os.getenv(f'TPK_SKIP_DOWNLOAD_{media_type.upper()}', '').lower()
    if value == 'true':
        skip_download_media_types.append(media_type)
logger.info(f"🔹 Media types to skip downloading: {skip_download_media_types}")

# File size settings
skip_download_bigger = 987654321
env_max_file_size = os.getenv('TPK_SKIP_DOWNLOAD_BIGGER', '')
if env_max_file_size.isdigit():
    skip_download_bigger = max(10, min(int(env_max_file_size), skip_download_bigger))
logger.info(f"🔹 Max file size to skip downloading: {skip_download_bigger}")

# Thumbnail settings
skip_download_thumbnail = os.getenv('TPK_SKIP_DOWNLOAD_THUMBNAIL', '').lower() == 'true'
logger.info(f"🔹 Skip thumbnail download: {skip_download_thumbnail}")

# Encryption key and IV
encrypt_aes_key_base64 = os.getenv('TPK_ENCRYPT_AES_KEY_BASE64', '')
encrypt_aes_iv_base64 = os.getenv('TPK_ENCRYPT_AES_IV_BASE64', '')

if encrypt_aes_key_base64 and encrypt_aes_iv_base64:
    logger.info("🔹Encryption key and IV are set.")
else:
    logger.error("🔹 Encryption key or IV is not set!")

# Function definitions
async def update_chat_about_info(chat: Chat, chat_dir: pathlib.Path, encryption_enabled=False):
    logger.debug(f"🔹 Updating chat info for chat ID {chat.id}")
    about_path = chat_dir / 'about.yaml'
    last_title = ''
    if about_path.exists():
        last_title = await read_yaml(about_path)

    if last_title == chat.title:
        logger.debug("🔹 Chat title unchanged; skipping update.")
        return

    attributes = ['id', 'title', 'full_name', 'username', 'last_name', 'first_name']
    context = {attr: getattr(chat, attr) for attr in attributes if hasattr(chat, attr)}

    if encryption_enabled:
        logger.info("🔹 Applying encryption to chat info.")
        for key in context:
            context[key] = await encrypt_aes(encrypt_aes_key_base64, encrypt_aes_iv_base64, str(context[key]))
        context['encryption'] = f'aes-iv-{encrypt_aes_iv_base64}'

    await write_yaml(about_path, context)

def get_real_chat_id(chat_id_raw: int) -> int:
    return -chat_id_raw - 1000000000000

async def get_extension_media_heavy_object(_media_type: str, media_obj: Video | Audio | Document | PhotoSize) -> str:
    # Logic as before, replace print statements with logger.debug or logger.error
    ...

async def make_file_download(media_obj: any, file_size: int, path_media_obj: pathlib.Path):
    try:
        _file = await media_obj.get_file()
        await _file.download_to_drive(path_media_obj)
        logger.info(f"🔹 File downloaded to: {path_media_obj}")
    except Exception as e:
        logger.error(f"🔹 Error downloading file to {path_media_obj}: {e}")

def identify_media_type(message: Message) -> Optional[str]:
    for _media_type in MEDIA_TYPES_ALL:
        if hasattr(message, _media_type) and getattr(message, _media_type):
            return _media_type
    return ''

async def handler_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post:
        return

    message = update.channel_post
    logger.info(f"Processing message ID: {message.message_id}")
    # Logic as before, replace print statements with logger methods

def run_bot():
    logger.info("🚀 Bot is starting...")
    application = ApplicationBuilder().token(token).build()
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handler_channel_post))
    application.run_polling()

def main():
    run_bot()

if __name__ == '__main__':
    main()
