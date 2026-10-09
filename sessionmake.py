from telethon import TelegramClient

# Данные из твоего config.py или .env
api_id = 1234567  # твой API_ID
api_hash = 'твой_api_hash'

# Имя файла сессии (создастся my_session.session)
client = TelegramClient('my_session', api_id, api_hash)

async def main():
    await client.start()
    print("Файл сессии успешно создан!")
    await client.disconnect()

with client:
    client.loop.run_until_complete(main())