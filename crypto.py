from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64



def aes_encrypt_decrypt_demo():
    # Исходная строка для шифрования
    plaintext = "Рождественская елка"
    print("Исходный текст:", plaintext)

    # Получение ключа и IV из глобальных переменных
    key = base64.b64decode(SAVED_KEY_BASE64)
    iv = base64.b64decode(SAVED_IV_BASE64)

    # Шифрование
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    ciphertext_str = base64.b64encode(ciphertext).decode('utf-8')
    print("Зашифрованный текст (Base64):", ciphertext_str)

    # Расшифровка
    decipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_text = unpad(decipher.decrypt(base64.b64decode(ciphertext_str)), AES.block_size).decode('utf-8')
    print("Расшифрованный текст:", decrypted_text)


# Запуск примера
if __name__ == "__main__":
    aes_encrypt_decrypt_demo()