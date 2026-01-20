import asyncio
import os
import time
from pathlib import Path


async def cleanup_temp(max_age_seconds: int = 3600) -> None:
    tmp_dir = Path(os.getenv("TMP", "/tmp"))
    if not tmp_dir.exists():
        return
    now = time.time()
    for item in tmp_dir.glob("xbot_*"):
        try:
            if now - item.stat().st_mtime > max_age_seconds:
                item.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            continue
    await asyncio.sleep(0)
