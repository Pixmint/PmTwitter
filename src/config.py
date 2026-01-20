import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    BOT_TOKEN: str
    MODE: str = "polling"
    TELEGRAM_USER_IDS: Optional[list[int]] = None
    REPLY_IN_GROUPS: bool = False
    COMPRESS_MEDIA: bool = True
    MAX_MEDIA_MB: int = 20
    FX_BASE_URL: str = "https://fxtwitter.com"
    INCLUDE_QUOTED_MEDIA: bool = False
    DEFAULT_TRANSLATE_LANG: str = "off"
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_SECONDS: int = 5
    RATE_LIMIT_CHAT_SECONDS: int = 3
    
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
        
        return cls(
            BOT_TOKEN=bot_token,
            MODE=os.getenv("MODE", "polling"),
            TELEGRAM_USER_IDS=user_ids,
            REPLY_IN_GROUPS=os.getenv("REPLY_IN_GROUPS", "0") == "1",
            COMPRESS_MEDIA=os.getenv("COMPRESS_MEDIA", "1") == "1",
            MAX_MEDIA_MB=int(os.getenv("MAX_MEDIA_MB", "20")),
            FX_BASE_URL=os.getenv("FX_BASE_URL", "https://fxtwitter.com").rstrip('/'),
            INCLUDE_QUOTED_MEDIA=os.getenv("INCLUDE_QUOTED_MEDIA", "0") == "1",
            DEFAULT_TRANSLATE_LANG=os.getenv("DEFAULT_TRANSLATE_LANG", "off"),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        )

config = Config.from_env()