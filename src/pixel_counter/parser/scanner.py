from __future__ import annotations

from pathlib import Path


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def natural_key(path: Path) -> list[object]:
    key: list[object] = []
    current = ""
    for char in path.stem:
        if char.isdigit():
            current += char
            continue
        if current:
            key.append(int(current))
            current = ""
        key.append(char.lower())
    if current:
        key.append(int(current))
    return key


def scan_image_files(image_dir: Path) -> list[Path]:
    if not image_dir.exists():
        return []
    files = [path for path in image_dir.iterdir() if path.suffix.lower() in SUPPORTED_EXTENSIONS]
    return sorted(files, key=natural_key)
