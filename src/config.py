import os
from dataclasses import dataclass, field
from typing import Optional

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
    
    @classmethod
    def from_env(cls):
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN обязателен")
        
        user_ids_str = os.getenv("TELEGRAM_USER_IDS", "")
        user_ids = None
        if user_ids_str:
            try:
                user_ids = [int(uid.strip()) for uid in user_ids_str.split(",") if uid.strip()]
            except ValueError:
                print("Предупреждение: неверный формат TELEGRAM_USER_IDS")

        retry_status_codes_str = os.getenv("RETRY_STATUS_CODES", "408,429")
        retry_status_codes = []
        if retry_status_codes_str:
            for part in retry_status_codes_str.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    retry_status_codes.append(int(part))
                except ValueError:
                    print("Предупреждение: неверный формат RETRY_STATUS_CODES")
        
        return cls(
            BOT_TOKEN=bot_token,
            MODE=os.getenv("MODE", "polling"),
            TELEGRAM_USER_IDS=user_ids,
            REPLY_IN_GROUPS=os.getenv("REPLY_IN_GROUPS", "0") == "1",
            REMOVE_MESSAGE_IN_GROUPS=os.getenv("REMOVE_MESSAGE_IN_GROUPS", "0") == "1",
            COMPRESS_MEDIA=os.getenv("COMPRESS_MEDIA", "1") == "1",
            MAX_MEDIA_MB=int(os.getenv("MAX_MEDIA_MB", "20")),
            FX_BASE_URL=os.getenv("FX_BASE_URL", "https://fxtwitter.com").rstrip('/'),
            INCLUDE_QUOTED_MEDIA=os.getenv("INCLUDE_QUOTED_MEDIA", "0") == "1",
            DEFAULT_TRANSLATE_LANG=os.getenv("DEFAULT_TRANSLATE_LANG", "off"),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            RATE_LIMIT_SECONDS=int(os.getenv("RATE_LIMIT_SECONDS", "5")),
            RATE_LIMIT_CHAT_SECONDS=int(os.getenv("RATE_LIMIT_CHAT_SECONDS", "3")),
            REPLY_TO_MESSAGE=os.getenv("REPLY_TO_MESSAGE", "1") == "1",
            CAPTION_ABOVE_MEDIA=os.getenv("CAPTION_ABOVE_MEDIA", "1") == "1",
            DUMP_TWEET_HTML=os.getenv("DUMP_TWEET_HTML", "0") == "1",
            RETRY_MAX_ATTEMPTS=int(os.getenv("RETRY_MAX_ATTEMPTS", "3")),
            RETRY_WAIT_MIN=float(os.getenv("RETRY_WAIT_MIN", "0.5")),
            RETRY_WAIT_MAX=float(os.getenv("RETRY_WAIT_MAX", "4.0")),
            RETRY_WAIT_MULTIPLIER=float(os.getenv("RETRY_WAIT_MULTIPLIER", "0.5")),
            RETRY_STATUS_CODES=retry_status_codes,
        )

config = Config.from_env()
