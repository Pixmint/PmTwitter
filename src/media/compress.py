import os
import tempfile
import logging
import subprocess
from PIL import Image
from src.config import config
from src.media.download import get_file_size_mb

logger = logging.getLogger(__name__)

def compress_image(input_path: str, max_size_mb: float = None) -> str:
    """Сжимает изображение"""
    if max_size_mb is None:
        max_size_mb = config.MAX_MEDIA_MB
    
    if not config.COMPRESS_MEDIA:
        return input_path
    
    current_size = get_file_size_mb(input_path)
    
    if current_size <= max_size_mb:
        return input_path
    
    try:
        img = Image.open(input_path)
        
        # Конвертируем в RGB если нужно
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        # Создаём новый временный файл
        fd, output_path = tempfile.mkstemp(suffix=".jpg", dir="/tmp", prefix="compressed_")
        os.close(fd)
        
        # Начинаем с качества 85
        quality = 85
        img.save(output_path, "JPEG", quality=quality, optimize=True)
        
        # Уменьшаем качество пока не достигнем нужного размера
        while get_file_size_mb(output_path) > max_size_mb and quality > 30:
            quality -= 5
            img.save(output_path, "JPEG", quality=quality, optimize=True)
        
        logger.info(f"Изображение сжато: {current_size:.2f}MB -> {get_file_size_mb(output_path):.2f}MB")
        return output_path
        
    except Exception as e:
        logger.error(f"Ошибка сжатия изображения: {e}")
        return input_path

def compress_video(input_path: str, max_size_mb: float = None) -> str:
    """Сжимает видео через ffmpeg (если доступен)"""
    if max_size_mb is None:
        max_size_mb = config.MAX_MEDIA_MB
    
    if not config.COMPRESS_MEDIA:
        return input_path
    
    current_size = get_file_size_mb(input_path)
    
    if current_size <= max_size_mb:
        return input_path
    
    # Проверяем наличие ffmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("ffmpeg не найден, сжатие видео недоступно")
        return input_path
    
    try:
        fd, output_path = tempfile.mkstemp(suffix=".mp4", dir="/tmp", prefix="compressed_")
        os.close(fd)
        
        # Простое сжатие через ffmpeg
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264',
            '-crf', '28',
            '-preset', 'fast',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        
        if result.returncode == 0 and os.path.exists(output_path):
            new_size = get_file_size_mb(output_path)
            logger.info(f"Видео сжато: {current_size:.2f}MB -> {new_size:.2f}MB")
            return output_path
        else:
            logger.error("Ошибка сжатия видео через ffmpeg")
            return input_path
            
    except Exception as e:
        logger.error(f"Ошибка сжатия видео: {e}")
        return input_path