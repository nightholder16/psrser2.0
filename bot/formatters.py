from __future__ import annotations

from datetime import datetime
from html import escape

from bot.emojis import e
from parser.serializers import is_ton_listing, normalize_owner_username
from config import Settings

# Замени на свою ссылку/юзернейм
AUTHOR_NAME = "NightHolder"
AUTHOR_URL = "https://t.me/Night_Holder"


def _model_name(attrs: list[str] | None) -> str | None:
    for raw in attrs or []:
        if isinstance(raw, str) and raw.startswith("model:"):
            name = raw[6:].strip()
            if name:
                return name
    return None


def alert_price_label(row: dict) -> str:
    stars = row.get("resell_stars")
    ton_nano = row.get("resell_ton")

    if stars is not None and ton_nano is not None:
        return f"{int(stars)} Stars / {float(ton_nano) / 1_000_000_000:.2f} TON"
    if is_ton_listing(row) and ton_nano is not None:
        return f"{float(ton_nano) / 1_000_000_000:.2f} TON"
    if stars is not None:
        return f"{int(stars)} Stars"
    if ton_nano is not None:
        return f"{float(ton_nano) / 1_000_000_000:.2f} TON"
    return "?"


def _messages_label(paid_stars: int | None) -> str:
    if paid_stars is None:
        return "?"
    if paid_stars <= 0:
        return "Free"
    return f"Paid ({paid_stars} Stars)"


def _status_label(premium: bool | None) -> str:
    if premium is True:
        return "Premium"
    if premium is False:
        return "No premium"
    return "?"


def new_listing_text(row: dict, settings: Settings | None = None) -> str:
    del settings
    title = escape(row.get("title") or "NFT")
    slug = row.get("slug") or ""
    owner = normalize_owner_username(row.get("owner_name"))
    owner_id = row.get("owner_user_id")
    model = _model_name(row.get("attributes_json") or [])
    level = row.get("owner_level")
    paid = row.get("owner_paid_messages_stars")
    premium = row.get("owner_premium")
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    nft_url = f"https://t.me/nft/{escape(slug)}" if slug else ""

    # Продавец — @username или id
    if owner and owner_id:
        seller = f"@{escape(owner)} (<code>{int(owner_id)}</code>)"
    elif owner:
        seller = f"@{escape(owner)}"
    elif owner_id:
        seller = f"<code>{int(owner_id)}</code>"
    else:
        seller = "?"

    lines = [
        f'{e("sparkles")} <b>NEW GIFT LISTING :)</b>',
        "",
        f'{e("gift")} <b>Gift:</b> {title}',
        f'{e("coin")} <b>Price:</b> {escape(alert_price_label(row))}',
    ]
    if model:
        lines.append(f'{e("tag")} <b>Model:</b> {escape(model)}')
    lines.append(
        f'{e("chart")} <b>Level:</b> {escape(str(level) if level is not None else "?")}'
    )
    lines.append(f'{e("megaphone")} <b>Message:</b> {escape(_messages_label(paid))}')
    lines.append(f'{e("status")} <b>Status:</b> {escape(_status_label(premium))}')
    lines.append(f'{e("user")} <b>Продавец:</b> {seller}')
    if slug:
        lines.append(f'🔗 <a href="{nft_url}">{escape(slug)}</a>')
    lines.append(f'{e("clock")} {escape(now)}')
    lines.append("")
    lines.append(
        f'Made with love by <a href="{AUTHOR_URL}"><b>{escape(AUTHOR_NAME)}</b></a>'
    )
    return "\n".join(lines)


def admin_status_text(
    *,
    baseline_done: bool,
    seen: int,
    topics: int,
    sessions_alive: int,
    sessions_total: int,
) -> str:
    return (
        f"{e('status')} <b>Market Forum Alerts</b>\n\n"
        f"Сессии: <b>{sessions_alive}/{sessions_total}</b>\n"
        f"Baseline: {'✅ готов' if baseline_done else '⏳ первый скан'}\n"
        f"Запомнено лотов: <b>{seen}</b>\n"
        f"Топиков: <b>{topics}</b>\n\n"
        "Бот шлёт новые лоты в топики чата по цене.\n"
        "Аккаунты для парсинга — кнопка ниже."
    )


def sessions_list_text(items: list[dict]) -> str:
    lines = [f"{e('user')} <b>Аккаунты парсера</b>\n"]
    if not items:
        lines.append("Пока нет сессий.\nНажмите «Добавить .session».")
        return "\n".join(lines)
    for i, row in enumerate(items, 1):
        status = "✅" if row.get("alive") else "❌"
        username = row.get("username")
        who = f"@{escape(username)}" if username else escape(row["label"])
        uid = row.get("tg_user_id")
        uid_part = f" · <code>{uid}</code>" if uid else ""
        lines.append(f"{i}. {status} {who}{uid_part}")
    lines.append("\nПодарки делятся между живыми сессиями поровну.")
    return "\n".join(lines)


def session_add_prompt_text() -> str:
    return (
        f"{e('gift')} <b>Добавить аккаунт</b>\n\n"
        "Отправьте один или несколько файлов <code>.session</code> (Telethon) — "
        "по одному или альбомом.\n"
        "Сессии должны быть уже авторизованы.\n\n"
        "Когда закончите — нажмите «Готово»."
    )


def session_phone_prompt_text() -> str:
    return (
        f"{e('user')} <b>Вход по номеру</b>\n\n"
        "Отправьте номер в формате <code>+79991234567</code>"
    )


def session_code_prompt_text(code: str) -> str:
    dots = code + "•" * max(0, 5 - len(code))
    return (
        f"{e('clock')} <b>Код из Telegram</b>\n\n"
        f"Введите код на клавиатуре:\n<code>{escape(dots)}</code>"
    )


def session_password_prompt_text() -> str:
    return (
        f"{e('cancel')} <b>Двухфакторный пароль</b>\n\n"
        "Отправьте пароль облачного пароля обычным сообщением."
    )


def session_auth_failed_text(reason: str) -> str:
    return f"{e('cancel')} {escape(reason)}"


def session_added_text(*, label: str, username: str | None, tg_user_id: int | None) -> str:
    who = f"@{escape(username)}" if username else escape(label)
    uid = f" (<code>{tg_user_id}</code>)" if tg_user_id else ""
    return f"{e('done')} Аккаунт добавлен: <b>{who}</b>{uid}"


def session_add_failed_text(error: str) -> str:
    return f"{e('cancel')} Не удалось добавить сессию.\n<code>{escape(error[:300])}</code>"


def session_batch_upload_result_text(results: list[dict]) -> str:
    ok_count = sum(1 for r in results if r.get("ok"))
    fail_count = len(results) - ok_count
    lines = [
        f"{e('gift')} <b>Загрузка сессий</b>\n",
        f"Добавлено: <b>{ok_count}</b> · ошибок: <b>{fail_count}</b>\n",
    ]
    for row in results:
        name = escape(str(row.get("file_name") or row.get("label") or "?"))
        if row.get("ok"):
            username = row.get("username")
            label = row.get("label")
            who = f"@{escape(username)}" if username else escape(str(label or "?"))
            uid = row.get("tg_user_id")
            uid_part = f" (<code>{uid}</code>)" if uid else ""
            lines.append(f"✅ {name} → <b>{who}</b>{uid_part}")
        else:
            err = escape(str(row.get("error") or "unknown")[:200])
            lines.append(f"❌ {name} — <code>{err}</code>")
    lines.append("\nМожно отправить ещё файлы или нажать «Готово».")
    return "\n".join(lines)


def session_deleted_text(label: str) -> str:
    return f"{e('done')} Аккаунт удалён: <code>{escape(label)}</code>"


def session_delete_pick_text() -> str:
    return f"{e('cancel')} Выберите аккаунт для удаления:"