import base64
import pathlib
from typing import Optional

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


async def encrypt_aes_bytes(key_base64: str, iv_base64: str, plaintext_bytes: bytes) -> Optional[bytes]:
    if not key_base64 or not iv_base64:
        print('🔴 No key_base64 and iv_base64 is set!!!! Encription to void and return this text ')
        return

    # Получение ключа и IV из глобальных переменных
    key = base64.b64decode(key_base64)
    iv = base64.b64decode(iv_base64)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext_bytes, AES.block_size))
    ciphertext_bytes = base64.b64encode(ciphertext)

    return ciphertext_bytes


async def encrypt_aes(key_base64: str, iv_base64: str, plaintext: str) -> str:
    ciphertext_bytes = await encrypt_aes_bytes(key_base64, iv_base64, plaintext.encode('utf-8'))
    return  ciphertext_bytes.decode('utf-8')


async def encrypt_aes_file(key_base64: str, iv_base64: str, path: pathlib.Path, output_path: pathlib.Path) -> Optional[pathlib.Path]:
    if not key_base64 or not iv_base64:
        print('🔴 No key_base64 and iv_base64 is set!!!! Encription to void and return this text ')
        return

    if not path.exists():
        return

    with path.open('rb') as f:
        bytes_text = f.read()

    bytes_encrypted_text = await encrypt_aes_bytes(key_base64, iv_base64, bytes_text)

    with output_path.open('wb') as f:
        f.write(bytes_encrypted_text)

    return output_path