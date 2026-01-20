import asyncio
import json
from pathlib import Path


class SettingsStore:
    def __init__(self, path: str | None = None) -> None:
        self._path = Path(path or "data/settings.json")
        self._lock = asyncio.Lock()
        self._data: dict[str, dict[str, str]] = {}

    async def load(self) -> None:
        async with self._lock:
            if not self._path.exists():
                self._path.parent.mkdir(parents=True, exist_ok=True)
                self._data = {}
                return
            try:
                self._data = json.loads(self._path.read_text(encoding="utf8"))
            except json.JSONDecodeError:
                self._data = {}

    async def save(self) -> None:
        async with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf8")

    async def get_translate(self, user_id: int, default: str) -> str:
        async with self._lock:
            return self._data.get(str(user_id), {}).get("translate", default)

    async def set_translate(self, user_id: int, lang: str) -> None:
        async with self._lock:
            entry = self._data.setdefault(str(user_id), {})
            entry["translate"] = lang
