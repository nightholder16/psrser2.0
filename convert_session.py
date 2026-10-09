from telethon import TelegramClient
from telethon.sessions import StringSession

# 1. Вставь свою строковую сессию сюда
STRING_SESSION = "1ApWapzMBuzx1WVRPhzK9-GYJv7L4QqsR_AlLm2DtATUMhB0sTKs0qz3RJxwOwCh8oxDS1Ulwl7e0X6xq3kp89w6-71X3VgYCD-TNbfb_JqfcSuSBKfK_sR9ORi8njZieH04SmRLsbBlcrMU4M9Pzr4apI0pXuKskv9DzL2ZfR08gwlAErt_vngtvyn_Fgyj7JxYPnD_SgdRRhuy_cKXLJWOn9U8zPueEBLIOUScVWsnbnOudfc66a0XHmnq3hW8gbel4JChuQX51qCpjH9WkU-j9obwPWLoeitGm5YhY0VCDEGvzYfqtX6KlWiKIPgZkbFTbJ7tz0sZNZ6nhwh-9m8OpdQ2Yj5I="

# 2. Укажи свои API_ID и API_HASH (из .env или config.py)
API_ID = 1234567
API_HASH = "e315cef1c60a999f6ee0466fb92a2793"

# 3. Имя файла, который создастся в папке data/sessions/
# Лучше сразу использовать ID аккаунта, но можно любое
SESSION_FILE_NAME = "my_account"


async def main():
    print("Подключаюсь по строковой сессии...")
    # Создаём клиента из строки (только для чтения)
    source_client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

    # Создаём клиента, который будет писать в файл
    target_client = TelegramClient(f"data/sessions/{SESSION_FILE_NAME}", API_ID, API_HASH)

    try:
        await source_client.connect()
        if not await source_client.is_user_authorized():
            print("❌ Строка недействительна или это не StringSession Telethon.")
            return

        me = await source_client.get_me()
        print(f"✅ Строка рабочая. Аккаунт: {me.first_name} (@{me.username}, ID: {me.id})")

        # Копируем данные авторизации в файловую сессию
        await target_client.connect()
        target_client.session.set_dc(
            source_client.session.dc_id,
            source_client.session.server_address,
            source_client.session.port
        )
        target_client.session.auth_key = source_client.session.auth_key
        target_client.session.save()  # Принудительно сохраняем на диск

        print(f"✅ Файл сессии создан: data/sessions/{SESSION_FILE_NAME}.session")
        print("Теперь можно запускать main.py")

    finally:
        await source_client.disconnect()
        await target_client.disconnect()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())