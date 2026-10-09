from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import BaseFilter, Command, CommandObject
from aiogram.types import Message, TelegramObject

from config import Settings
from storage.blacklist import Blacklist

logger = logging.getLogger(__name__)
router = Router()


class AdminOnly(BaseFilter):
    async def __call__(self, event: TelegramObject, settings: Settings) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and settings.is_admin(user.id))


router.message.filter(AdminOnly())


def _help_text() -> str:
    return (
        "🛠 <b>Управление чёрным списком</b>\n\n"
        "Все команды — только для админов.\n\n"
        "• <code>/blacklist</code> — показать список\n"
        "• <code>/blacklist_add @username</code> — добавить юзера по нику\n"
        "• <code>/blacklist_add 123456789</code> — добавить по ID\n"
        "• <code>/blacklist_rm @username</code> — убрать по нику\n"
        "• <code>/blacklist_rm 123456789</code> — убрать по ID\n\n"
        "Листинги этих юзеров <b>не будут</b> отправляться в группу."
    )


@router.message(Command("blacklist"))
async def cmd_blacklist(message: Message, blacklist: Blacklist) -> None:
    data = blacklist.list_all()
    usernames = data["usernames"]
    ids = data["user_ids"]

    lines = [f"🚫 <b>Чёрный список</b>\n"]
    if not usernames and not ids:
        lines.append("Пусто. Добавь через <code>/blacklist_add</code>.")
    else:
        if usernames:
            lines.append("<b>Юзернеймы:</b>")
            for u in usernames:
                lines.append(f"• @{u}")
        if ids:
            lines.append("\n<b>ID:</b>")
            for i in ids:
                lines.append(f"• <code>{i}</code>")
    lines.append("\n" + _help_text())
    await message.answer("\n".join(lines))


@router.message(Command("blacklist_add"))
async def cmd_blacklist_add(
    message: Message,
    command: CommandObject,
    blacklist: Blacklist,
) -> None:
    arg = (command.args or "").strip()
    if not arg:
        await message.answer("Использование: <code>/blacklist_add @username</code> или <code>/blacklist_add 123456789</code>")
        return
    if arg.isdigit():
        uid = int(arg)
        added = blacklist.add_user_id(uid)
        if added:
            await message.answer(f"✅ Добавлен ID <code>{uid}</code> в чёрный список.")
        else:
            await message.answer(f"⚠️ ID <code>{uid}</code> уже в списке.")
        return

    username = arg.lstrip("@")
    if not username:
        await message.answer("Пустой юзернейм.")
        return
    added = blacklist.add_username(username)
    if added:
        await message.answer(f"✅ Добавлен @{username} в чёрный список.")
    else:
        await message.answer(f"⚠️ @{username} уже в списке.")


@router.message(Command("blacklist_rm"))
async def cmd_blacklist_rm(
    message: Message,
    command: CommandObject,
    blacklist: Blacklist,
) -> None:
    arg = (command.args or "").strip()
    if not arg:
        await message.answer("Использование: <code>/blacklist_rm @username</code> или <code>/blacklist_rm 123456789</code>")
        return
    if arg.isdigit():
        uid = int(arg)
        removed = blacklist.remove_user_id(uid)
        if removed:
            await message.answer(f"✅ Удалён ID <code>{uid}</code> из чёрного списка.")
        else:
            await message.answer(f"⚠️ ID <code>{uid}</code> не найден в списке.")
        return

    username = arg.lstrip("@")
    removed = blacklist.remove_username(username)
    if removed:
        await message.answer(f"✅ Удалён @{username} из чёрного списка.")
    else:
        await message.answer(f"⚠️ @{username} не найден в списке.")