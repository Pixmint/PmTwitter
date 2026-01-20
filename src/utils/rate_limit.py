import asyncio
import time


class RateLimiter:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._user_last: dict[int, float] = {}
        self._chat_last: dict[int, float] = {}

    async def allow(self, user_id: int, chat_id: int, user_window: float = 5.0, chat_window: float = 2.0) -> bool:
        now = time.monotonic()
        async with self._lock:
            last_user = self._user_last.get(user_id, 0.0)
            last_chat = self._chat_last.get(chat_id, 0.0)
            if now - last_user < user_window:
                return False
            if now - last_chat < chat_window:
                return False
            self._user_last[user_id] = now
            self._chat_last[chat_id] = now
            return True
