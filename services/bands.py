from __future__ import annotations

from parser.serializers import format_ton_amount, is_ton_listing
from config import PriceBand, Settings
from services.gift_floors import gift_floor_ton


OTHER_BAND_KEY = "other"
BLACK_ONYX_BAND_KEY = "black_onyx"
COUNTRIES_BAND_KEY = "countries"
NANOTON = 1_000_000_000

_BLACK_ONYX_BACKDROPS = {"black", "onyx"}

# Диапазоны Unicode для CJK (китайский/японский) и арабского
_CJK_RANGES = (
    (0x4E00, 0x9FFF),   # CJK Unified Ideographs
    (0x3400, 0x4DBF),   # CJK Extension A
    (0x3040, 0x309F),   # Hiragana
    (0x30A0, 0x30FF),   # Katakana
    (0xAC00, 0xD7AF),   # Hangul (корейский, на всякий)
)
_ARABIC_RANGES = (
    (0x0600, 0x06FF),   # Arabic
    (0x0750, 0x077F),   # Arabic Supplement
    (0xFB50, 0xFDFF),   # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF),   # Arabic Presentation Forms-B
)


def ton_nano_to_stars(ton_nano: int, stars_per_ton: float) -> float:
    return (float(ton_nano) / NANOTON) * float(stars_per_ton)


def _has_black_or_onyx_backdrop(listing: dict) -> bool:
    for attr in listing.get("attributes_json") or []:
        if not isinstance(attr, str):
            continue
        if not attr.startswith("backdrop:"):
            continue
        name = attr[len("backdrop:"):].strip().casefold()
        if name in _BLACK_ONYX_BACKDROPS:
            return True
    return False


def is_country_username(username: str | None) -> bool:
    """True, если в нике есть CJK или арабские символы."""
    if not username:
        return False
    for ch in username:
        cp = ord(ch)
        for lo, hi in _CJK_RANGES:
            if lo <= cp <= hi:
                return True
        for lo, hi in _ARABIC_RANGES:
            if lo <= cp <= hi:
                return True
    return False


def match_band(listing: dict, settings: Settings) -> PriceBand | None:
    value = gift_floor_ton(listing.get("title"))
    if value is None:
        return None

    for band in settings.price_bands:
        if band.currency != "ton":
            continue
        if value < band.min_value:
            continue
        if band.max_value is not None and value >= band.max_value:
            continue
        return band
    return None


def band_key_for_listing(listing: dict, settings: Settings) -> str:
    if _has_black_or_onyx_backdrop(listing):
        return BLACK_ONYX_BAND_KEY
    band = match_band(listing, settings)
    if band is None:
        return OTHER_BAND_KEY
    # Для ценовых бэндов ниже 50 TON проверим «страновой» ник
    if band.min_value < 50 and is_country_username(listing.get("owner_name")):
        return COUNTRIES_BAND_KEY
    return band.key


def price_label(listing: dict, settings: Settings | None = None) -> str:
    stars = listing.get("resell_stars")
    ton_nano = listing.get("resell_ton")

    if is_ton_listing(listing) and ton_nano is not None:
        ton_txt = format_ton_amount(int(ton_nano))
        if settings is not None:
            eq = ton_nano_to_stars(int(ton_nano), settings.stars_per_ton)
            return f"{ton_txt} TON ≈ {eq:,.0f} ⭐"
        return f"{ton_txt} TON"

    if stars is not None and ton_nano is not None:
        ton_txt = format_ton_amount(int(ton_nano))
        return f"{int(stars):,} ⭐ / {ton_txt} TON"

    if stars is not None:
        return f"{int(stars):,} ⭐"
    return "?"


# ---------- Фильтры для дешёвых/средних лотов ----------

CHEAP_MID_MAX_LEVEL = 2
CHEAP_MID_MAX_GIFTS = 5
COUNTRY_MAX_LEVEL = 2
COUNTRY_MAX_GIFTS = 2


def is_cheap_or_mid_band(band_key: str) -> bool:
    """0-15 и 15-50 — сюда применяются строгие фильтры."""
    return band_key in ("ton:0-15", "ton:15-50")


def passes_cheap_mid_filters(listing: dict) -> bool:
    """True, если листинг проходит фильтры дешёвых/средних."""
    level = listing.get("owner_level")
    if level is not None and int(level) > CHEAP_MID_MAX_LEVEL:
        return False

    paid = listing.get("owner_paid_messages_stars")
    if paid is not None and int(paid) > 0:
        return False

    premium = listing.get("owner_premium")
    if premium is True:
        return False

    gifts = listing.get("owner_gifts_count")
    if gifts is not None and int(gifts) > CHEAP_MID_MAX_GIFTS:
        return False

    return True


def passes_country_filters(listing: dict) -> bool:
    """True, если листинг проходит фильтры «Разные страны»."""
    level = listing.get("owner_level")
    if level is not None and int(level) > COUNTRY_MAX_LEVEL:
        return False

    gifts = listing.get("owner_gifts_count")
    if gifts is not None and int(gifts) > COUNTRY_MAX_GIFTS:
        return False

    return True