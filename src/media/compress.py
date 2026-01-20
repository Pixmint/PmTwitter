import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


def size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def compress_image(path: Path, max_mb: int) -> Path:
    if size_mb(path) <= max_mb:
        return path
    img = Image.open(path)
    out_fd, out_path = tempfile.mkstemp(prefix="xbot_img_", suffix=".jpg")
    os.close(out_fd)
    img.convert("RGB").save(out_path, format="JPEG", quality=75, optimize=True)
    return Path(out_path)


def compress_video(path: Path, max_mb: int) -> Path:
    if size_mb(path) <= max_mb:
        return path
    if not shutil.which("ffmpeg"):
        return path
    out_fd, out_path = tempfile.mkstemp(prefix="xbot_vid_", suffix=".mp4")
    os.close(out_fd)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(path),
        "-vcodec",
        "libx264",
        "-crf",
        "28",
        "-preset",
        "veryfast",
        str(out_path),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if Path(out_path).exists() and size_mb(Path(out_path)) <= max_mb:
        return Path(out_path)
    return path
