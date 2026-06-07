import logging
import os
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ALLOWED_FX_HOSTS = {
    "fxtwitter.com",
    "fixupx.com",
    "vxtwitter.com",
}


def _parse_bool(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(name: str, default: int, min_value: int | None = None) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} должен быть целым числом") from exc
    if min_value is not None and value < min_value:
        raise ValueError(f"{name} должен быть >= {min_value}")
    return value


def _parse_float(name: str, default: float, min_value: float | None = None) -> float:
    raw = os.getenv(name, str(default))
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} должен быть числом") from exc
    if min_value is not None and value < min_value:
        raise ValueError(f"{name} должен быть >= {min_value}")
    return value


def _parse_user_ids() -> Optional[list[int]]:
    user_ids_str = os.getenv("TELEGRAM_USER_IDS", "")
    if not user_ids_str:
        return None
    try:
        return [int(uid.strip()) for uid in user_ids_str.split(",") if uid.strip()]
    except ValueError as exc:
        raise ValueError("TELEGRAM_USER_IDS должен быть списком числовых ID через запятую") from exc


def _parse_retry_status_codes() -> list[int]:
    retry_status_codes_str = os.getenv("RETRY_STATUS_CODES", "408,429")
    retry_status_codes: list[int] = []
    for part in retry_status_codes_str.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            retry_status_codes.append(int(part))
        except ValueError as exc:
            raise ValueError("RETRY_STATUS_CODES должен быть списком HTTP-кодов через запятую") from exc
    return retry_status_codes


def _parse_fx_base_url() -> str:
    raw_url = os.getenv("FX_BASE_URL", "https://fxtwitter.com").rstrip("/")
    parsed = urlparse(raw_url)
    if parsed.scheme != "https":
        raise ValueError("FX_BASE_URL должен использовать https")
    if parsed.netloc not in ALLOWED_FX_HOSTS:
        allowed = ", ".join(sorted(ALLOWED_FX_HOSTS))
        raise ValueError(f"FX_BASE_URL должен быть одним из: {allowed}")
    if parsed.path or parsed.query or parsed.fragment:
        raise ValueError("FX_BASE_URL должен содержать только схему и домен")
    return raw_url


@dataclass
class Config:
    BOT_TOKEN: str
    MODE: str = "polling"
    TELEGRAM_USER_IDS: Optional[list[int]] = None
    REPLY_IN_GROUPS: bool = False
    REMOVE_MESSAGE_IN_GROUPS: bool = False
    COMPRESS_MEDIA: bool = True
    MAX_MEDIA_MB: int = 20
    FX_BASE_URL: str = "https://fxtwitter.com"
    INCLUDE_QUOTED_MEDIA: bool = False
    DEFAULT_TRANSLATE_LANG: str = "off"
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_SECONDS: int = 5
    RATE_LIMIT_CHAT_SECONDS: int = 3
    REPLY_TO_MESSAGE: bool = True
    CAPTION_ABOVE_MEDIA: bool = True
    DUMP_TWEET_HTML: bool = False
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_WAIT_MIN: float = 0.5
    RETRY_WAIT_MAX: float = 4.0
    RETRY_WAIT_MULTIPLIER: float = 0.5
    RETRY_STATUS_CODES: list[int] = field(default_factory=lambda: [408, 429])
    TRANSLATE_SETTINGS_PATH: str = "/app/data/translate_settings.json"

    @classmethod
    def from_env(cls) -> "Config":
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN обязателен")

        mode = os.getenv("MODE", "polling")
        if mode not in {"polling", "webhook"}:
            raise ValueError("MODE должен быть polling или webhook")

        return cls(
            BOT_TOKEN=bot_token,
            MODE=mode,
            TELEGRAM_USER_IDS=_parse_user_ids(),
            REPLY_IN_GROUPS=_parse_bool("REPLY_IN_GROUPS"),
            REMOVE_MESSAGE_IN_GROUPS=_parse_bool("REMOVE_MESSAGE_IN_GROUPS"),
            COMPRESS_MEDIA=_parse_bool("COMPRESS_MEDIA", "1"),
            MAX_MEDIA_MB=_parse_int("MAX_MEDIA_MB", 20, min_value=1),
            FX_BASE_URL=_parse_fx_base_url(),
            INCLUDE_QUOTED_MEDIA=_parse_bool("INCLUDE_QUOTED_MEDIA"),
            DEFAULT_TRANSLATE_LANG=os.getenv("DEFAULT_TRANSLATE_LANG", "off").strip().lower(),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO").upper(),
            RATE_LIMIT_SECONDS=_parse_int("RATE_LIMIT_SECONDS", 5, min_value=0),
            RATE_LIMIT_CHAT_SECONDS=_parse_int("RATE_LIMIT_CHAT_SECONDS", 3, min_value=0),
            REPLY_TO_MESSAGE=_parse_bool("REPLY_TO_MESSAGE", "1"),
            CAPTION_ABOVE_MEDIA=_parse_bool("CAPTION_ABOVE_MEDIA", "1"),
            DUMP_TWEET_HTML=_parse_bool("DUMP_TWEET_HTML"),
            RETRY_MAX_ATTEMPTS=_parse_int("RETRY_MAX_ATTEMPTS", 3, min_value=1),
            RETRY_WAIT_MIN=_parse_float("RETRY_WAIT_MIN", 0.5, min_value=0),
            RETRY_WAIT_MAX=_parse_float("RETRY_WAIT_MAX", 4.0, min_value=0),
            RETRY_WAIT_MULTIPLIER=_parse_float("RETRY_WAIT_MULTIPLIER", 0.5, min_value=0),
            RETRY_STATUS_CODES=_parse_retry_status_codes(),
            TRANSLATE_SETTINGS_PATH=os.getenv(
                "TRANSLATE_SETTINGS_PATH",
                "/app/data/translate_settings.json",
            ),
        )


config = Config.from_env()
