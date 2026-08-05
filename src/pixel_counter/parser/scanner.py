from __future__ import annotations

import re
from pathlib import Path


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def natural_key(path: Path) -> tuple:
    parts = re.split(r"(\d+)", path.stem.lower())
    return tuple(int(p) if p.isdigit() else p for p in parts)


def scan_image_files(image_dir: Path) -> list[Path]:
    if not image_dir.exists():
        return []
    files = [path for path in image_dir.iterdir() if path.suffix.lower() in SUPPORTED_EXTENSIONS]
    return sorted(files, key=natural_key)
