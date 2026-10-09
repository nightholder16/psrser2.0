from __future__ import annotations

import logging
import re
from datetime import datetime
from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
)

CLAIM_CB = "claim:take"
_NFT_URL_RE = re.compile(r"https://t\.me/nft/[A-Za-z0-9_\-]+")

logger = logging.getLogger(__name__)
router = Router()

# Премиум-эмодзи для иконок кнопок
ICON_USER = "5870994129244131212"
ICON_LINK = "5870527201874546272"
ICON_CLAIM = "5453969572354878595"


def claim_kb(
    *,
    owner_username: str | None = None,
    owner_user_id: int | None = None,
    slug: str | None = None,
) -> InlineKeyboardMarkup:
    # Столбик: Owner, Gift Link, Занять лог
    rows: list[list[InlineKeyboardButton]] = []

    if owner_username:
        rows.append([
            InlineKeyboardButton(
                text="Owner",
                url=f"https://t.me/{owner_username}",
                icon_custom_emoji_id=ICON_USER,
            )
        ])
    elif owner_user_id:
        rows.append([
            InlineKeyboardButton(
                text="Owner",
                url=f"tg://user?id={owner_user_id}",
                icon_custom_emoji_id=ICON_USER,
            )
        ])

    if slug:
        rows.append([
            InlineKeyboardButton(
                text="Gift Link",
                url=f"https://t.me/nft/{slug}",
                icon_custom_emoji_id=ICON_LINK,
            )
        ])

    rows.append([
        InlineKeyboardButton(
            text="Занять лог",
            callback_data=CLAIM_CB,
            icon_custom_emoji_id=ICON_CLAIM,
            style="success",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def dm_kb(
    *,
    owner_username: str | None = None,
    owner_user_id: int | None = None,
    slug: str | None = None,
) -> InlineKeyboardMarkup:
    # Кнопки для ЛС: Профиль продавца + Открыть подарок (в столбик)
    rows: list[list[InlineKeyboardButton]] = []

    if owner_username:
        rows.append([
            InlineKeyboardButton(
                text="Профиль продавца",
                url=f"https://t.me/{owner_username}",
                icon_custom_emoji_id=ICON_USER,
            )
        ])
    elif owner_user_id:
        rows.append([
            InlineKeyboardButton(
                text="Профиль продавца",
                url=f"tg://user?id={owner_user_id}",
                icon_custom_emoji_id=ICON_USER,
            )
        ])

    if slug:
        rows.append([
            InlineKeyboardButton(
                text="Открыть подарок",
                url=f"https://t.me/nft/{slug}",
                icon_custom_emoji_id=ICON_LINK,
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def claimed_text(username: str | None, *, user_id: int, full_name: str | None) -> str:
    if username:
        return f"Занято @{escape(username)}"
    name = (full_name or "").strip() or str(user_id)
    return f"Занято <b>{escape(name)}</b> (<code>{user_id}</code>)"


def _extract_seller_from_text(text: str) -> tuple[str | None, int | None]:
    """Вытаскивает @username и/или id продавца из текста листинга."""
    owner_name: str | None = None
    owner_id: int | None = None

    m = re.search(r"@([A-Za-z][A-Za-z0-9_]{3,31})", text)
    if m:
        owner_name = m.group(1)

    m = re.search(r"\((\d{5,})\)", text)
    if m:
        try:
            owner_id = int(m.group(1))
        except ValueError:
            pass

    return owner_name, owner_id


def _extract_slug_from_text(text: str) -> str | None:
    m = _NFT_URL_RE.search(text)
    if not m:
        return None
    return m.group(0).rsplit("/", 1)[-1]


def _build_dm_text(original: str) -> str:
    """Собирает текст для ЛС: шапка + листинг."""
    return "🎁 <b>Ты занял лот</b>\n\n" + original


async def _send_claim_copy(callback: CallbackQuery, original: str) -> bool:
    user = callback.from_user
    if user is None or not original:
        return False

    owner_name, owner_id = _extract_seller_from_text(original)
    slug = _extract_slug_from_text(original)
    text = _build_dm_text(original)

    # Кнопки в ЛС: Профиль продавца + Открыть подарок
    markup = dm_kb(
        owner_username=owner_name,
        owner_user_id=owner_id,
        slug=slug,
    )

    kwargs: dict = {
        "chat_id": user.id,
        "text": text,
        "reply_markup": markup,
    }
    if slug:
        kwargs["link_preview_options"] = LinkPreviewOptions(
            is_disabled=False,
            url=f"https://t.me/nft/{slug}",
            prefer_large_media=True,
        )

    try:
        await callback.bot.send_message(**kwargs)
        return True
    except TelegramForbiddenError:
        logger.info("Cannot DM claim copy to %s — bot not started", user.id)
        return False
    except Exception:
        logger.exception("Failed to DM claim copy to %s", user.id)
        return False


@router.callback_query(F.data == CLAIM_CB)
async def on_claim(callback: CallbackQuery) -> None:
    message = callback.message
    user = callback.from_user
    if message is None or user is None:
        await callback.answer()
        return

    original = (message.html_text or message.text or "").strip()
    if original.startswith("Занято") or message.reply_markup is None:
        await callback.answer("Уже занято", show_alert=True)
        return

    # Сначала пытаемся отправить копию в ЛС с кнопками
    dm_ok = await _send_claim_copy(callback, original)

    # В чате оставляем лот + пометку «Занял: @user · время»
    now = datetime.now().strftime("%H:%M:%S")
    if user.username:
        who = f"@{user.username}"
    else:
        who = (user.full_name or "").strip() or str(user.id)

    marked = original + f"\n\n🔒 <b>Занял:</b> {escape(who)} · {escape(now)}"

    try:
        await message.edit_text(marked, reply_markup=None)
    except Exception:
        await callback.answer("Уже занято", show_alert=True)
        return

    if dm_ok:
        await callback.answer("Занято. Копия лота — в личке.")
        return
    await callback.answer(
        "Занято. Напиши /start этому боту — в следующий раз пришлю копию в личку.",
        show_alert=True,
    )