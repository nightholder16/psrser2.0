from tdata_reader import read_tdata
from telethon import TelegramClient
from telethon.sessions import StringSession

# Путь к tdata третьего аккаунта
TDATA_PATH = r"C:\Users\user\Desktop\tg3\tdata"

acc = read_tdata(TDATA_PATH)
print(f"User ID: {acc.user_id}, DC: {acc.dc_id}")

session_string = acc.to_string_session()

client = TelegramClient(
    StringSession(session_string),
    **acc.as_init_connection_kwargs(),
)

async def save_to_file():
    await client.connect()
    me = await client.get_me()
    print(f"Готово: {me.first_name} (@{me.username}, id={me.id})")

    # Сохраняем в файл new_account3.session
    file_client = TelegramClient("new_account3", **acc.as_init_connection_kwargs())
    await file_client.connect()
    file_client.session.set_dc(
        client.session.dc_id,
        client.session.server_address,
        client.session.port,
    )
    file_client.session.auth_key = client.session.auth_key
    file_client.session.save()
    print("Файл new_account3.session создан")
    await file_client.disconnect()
    await client.disconnect()

import asyncio
asyncio.run(save_to_file())