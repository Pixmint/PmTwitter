import os
from dataclasses import dataclass


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    return value


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    bot_token: str
    mode: str
    telegram_user_ids: set[int]
    reply_in_groups: bool
    compress_media: bool
    max_media_mb: int
    fx_base_url: str
    fx_base_urls: list[str]
    include_quoted_media: bool
    default_translate_lang: str
    allow_x_fallback: bool
    enable_jina_fallback: bool
    log_level: str


def load_config() -> Config:
    token = _env("BOT_TOKEN", "")
    if not token:
        raise RuntimeError("Не задан BOT_TOKEN")

    ids_raw = _env("TELEGRAM_USER_IDS", "")
    ids = set()
    if ids_raw:
        for part in ids_raw.split(","):
            part = part.strip()
            if part:
                ids.add(int(part))

    fx_base_url = (_env("FX_BASE_URL", "https://fxtwitter.com") or "https://fxtwitter.com").rstrip("/")
    fx_list_raw = _env(
        "FX_BASE_URLS",
        "https://fxtwitter.com,https://fixupx.com,https://vxtwitter.com,https://twitfix.com",
    )
    fx_base_urls = [item.strip().rstrip("/") for item in (fx_list_raw or "").split(",") if item.strip()]
    if not fx_base_urls:
        fx_base_urls = [fx_base_url]
    return Config(
        bot_token=token,
        mode=_env("MODE", "polling") or "polling",
        telegram_user_ids=ids,
        reply_in_groups=_env_bool("REPLY_IN_GROUPS", False),
        compress_media=_env_bool("COMPRESS_MEDIA", False),
        max_media_mb=int(_env("MAX_MEDIA_MB", "20") or "20"),
        fx_base_url=fx_base_url,
        fx_base_urls=fx_base_urls,
        include_quoted_media=_env_bool("INCLUDE_QUOTED_MEDIA", False),
        default_translate_lang=_env("DEFAULT_TRANSLATE_LANG", "off") or "off",
        allow_x_fallback=_env_bool("ALLOW_X_FALLBACK", False),
        enable_jina_fallback=_env_bool("JINA_FALLBACK", True),
        log_level=_env("LOG_LEVEL", "INFO") or "INFO",
    )
