import os
import tempfile
import logging
from pathlib import Path
from typing import Optional
from src.twitter.fetcher import download_media

logger = logging.getLogger(__name__)

async def download_media_file(url: str, media_type: str = "photo") -> Optional[str]:
    """Скачивает медиа файл во временную директорию"""
    
    content = await download_media(url)
    if not content:
        return None
    
    # Определяем расширение
    if media_type == "video":
        ext = ".mp4"
    else:
        # Пытаемся определить по URL или используем .jpg
        if ".png" in url.lower():
            ext = ".png"
        elif ".webp" in url.lower():
            ext = ".webp"
        elif ".gif" in url.lower():
            ext = ".gif"
        else:
            ext = ".jpg"
    
    # Создаём временный файл
    try:
        fd, temp_path = tempfile.mkstemp(suffix=ext, dir="/tmp", prefix="tweet_media_")
        os.close(fd)
        
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Медиа скачано: {temp_path} ({len(content)} байт)")
        return temp_path
        
    except Exception as e:
        logger.error(f"Ошибка сохранения медиа: {e}")
        return None

def get_file_size_mb(file_path: str) -> float:
    """Возвращает размер файла в МБ"""
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0