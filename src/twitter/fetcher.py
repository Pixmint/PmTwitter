import asyncio
from dataclasses import dataclass

import httpx


@dataclass
class FetchResult:
    url: str
    text: str


@dataclass
class FetchJsonResult:
    url: str
    data: dict


async def fetch_html(
    url: str,
    timeout: float = 10.0,
    retries: int = 2,
    allow_x_fallback: bool = False,
) -> FetchResult:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                final_host = resp.url.host.lower() if resp.url.host else ""
                if final_host in {"x.com", "twitter.com"} and not allow_x_fallback:
                    raise RuntimeError("Фронтенд перенаправил на X, пробуем другое зеркало")
                return FetchResult(url=str(resp.url), text=resp.text)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            await asyncio.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"Не удалось получить данные: {last_exc}")


async def fetch_json(url: str, timeout: float = 10.0, retries: int = 2) -> FetchJsonResult:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                return FetchJsonResult(url=str(resp.url), data=resp.json())
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            await asyncio.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"Не удалось получить JSON: {last_exc}")
