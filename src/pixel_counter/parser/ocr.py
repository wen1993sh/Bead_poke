from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tempfile
from typing import Iterable

from PIL import Image

try:
    from rapidocr_onnxruntime import RapidOCR
except Exception:  # pragma: no cover - optional dependency on the target device
    RapidOCR = None


CODE_PATTERN = re.compile(r"\b([A-Z]\d{1,2})\b")
PAIR_PATTERN = re.compile(r"\b([A-Z]\d{1,2})\s*[:\-]?\s*(\d+)\b")
NUMBER_PATTERN = re.compile(r"\b(\d+)\b")


@dataclass(slots=True)
class OcrLine:
    text: str
    score: float = 0.0


_OCR_ENGINE = None


def get_ocr_engine():
    global _OCR_ENGINE
    if _OCR_ENGINE is not None:
        return _OCR_ENGINE
    if RapidOCR is None:
        raise RuntimeError("rapidocr-onnxruntime is not installed")
    _OCR_ENGINE = RapidOCR()
    return _OCR_ENGINE


def crop_to_temp_file(image_path: Path, box: tuple[int, int, int, int]) -> Path:
    with Image.open(image_path) as image:
        cropped = image.crop(box)
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        try:
            cropped.save(handle.name)
        finally:
            handle.close()
    return Path(handle.name)


def recognize_lines(image_path: Path) -> list[OcrLine]:
    engine = get_ocr_engine()
    raw_result = engine(str(image_path))
    if not raw_result:
        return []

    lines: list[OcrLine] = []
    for item in raw_result[0] if isinstance(raw_result, tuple) else raw_result:
        if not item:
            continue
        if isinstance(item, dict):
            text = str(item.get("text", ""))
            score = float(item.get("score", 0.0) or 0.0)
        else:
            text = str(item[1]) if len(item) > 1 else str(item[0])
            score = float(item[2]) if len(item) > 2 else 0.0
        if text.strip():
            lines.append(OcrLine(text=text.strip(), score=score))
    return lines


def extract_codes(lines: Iterable[OcrLine]) -> list[str]:
    codes: list[str] = []
    for line in lines:
        codes.extend(CODE_PATTERN.findall(line.text))
    return codes


def extract_count_pairs(lines: Iterable[OcrLine]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in lines:
        for code, value in PAIR_PATTERN.findall(line.text):
            counts[code] = int(value)
    return counts


def extract_axis_numbers(lines: Iterable[OcrLine]) -> int:
    numbers: list[int] = []
    for line in lines:
        numbers.extend(int(value) for value in NUMBER_PATTERN.findall(line.text))
    return max(numbers) if numbers else 0
