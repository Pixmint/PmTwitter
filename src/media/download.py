import asyncio
import os
import tempfile
from pathlib import Path

import httpx

from twitter.models import MediaItem


async def download_media(items: list[MediaItem]) -> list[tuple[MediaItem, Path]]:
    results: list[tuple[MediaItem, Path]] = []
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        for item in items:
            suffix = ".jpg" if item.type == "photo" else ".mp4"
            fd, path = tempfile.mkstemp(prefix="xbot_", suffix=suffix)
            os.close(fd)
            try:
                resp = await client.get(item.url, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                Path(path).write_bytes(resp.content)
                results.append((item, Path(path)))
            except Exception:  # noqa: BLE001
                if os.path.exists(path):
                    os.remove(path)
                continue
            await asyncio.sleep(0)
    return results
