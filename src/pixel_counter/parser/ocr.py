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

from pixel_counter.parser.preprocess import preprocess_for_ocr, preprocess_grayscale_only

CODE_PATTERN = re.compile(r"\b([A-Z]\d{1,2})\b")
RAW_CODE_PATTERN = re.compile(r"\b([A-Z][A-Z0-9]{1,3})\b")
# Use (?!\d) to prevent \d{1,2} from matching just the first digit of a
# multi-digit suffix (e.g. preventing "B1" from matching "B15")
PAIR_PATTERN = re.compile(r"\b([A-Z]\d{1,2})(?!\d)\s*[:\-]?\s*(\d+)\b")
RAW_PAIR_PATTERN = re.compile(r"\b([A-Z][A-Z0-9]{1,3})(?!\d)\s*[:\-]?\s*(\d+)\b")
NUMBER_PATTERN = re.compile(r"\b(\d+)\b")

# Minimum OCR confidence to accept a result
_MIN_CONFIDENCE = 0.5

_CODE_SUFFIX_MAP = {
    "O": "0",
    "D": "0",
    "Q": "0",
    "I": "1",
    "L": "1",
    "Z": "2",
    "S": "5",
}


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


def _normalize_code_token(token: str) -> str | None:
    text = str(token).upper().replace(" ", "").strip()
    matched = re.fullmatch(r"([A-Z])([A-Z0-9]{1,3})", text)
    if not matched:
        return None

    prefix, suffix = matched.groups()
    fixed_suffix = "".join(_CODE_SUFFIX_MAP.get(char, char) for char in suffix)
    normalized = f"{prefix}{fixed_suffix}"
    if CODE_PATTERN.fullmatch(normalized):
        return normalized
    return None


def _extract_normalized_codes(text: str) -> list[str]:
    normalized_codes: list[str] = []
    for raw in RAW_CODE_PATTERN.findall(text.upper()):
        normalized = _normalize_code_token(raw)
        if normalized:
            normalized_codes.append(normalized)
    return normalized_codes


def crop_to_temp_file(image_path: Path, box: tuple[int, int, int, int]) -> Path:
    with Image.open(image_path) as image:
        cropped = image.crop(box)
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        try:
            cropped.save(handle.name)
        finally:
            handle.close()
    return Path(handle.name)


def recognize_lines(
    image_path: Path,
    *,
    preprocess: str = "none",
    min_confidence: float = _MIN_CONFIDENCE,
) -> list[OcrLine]:
    """Run OCR on an image, optionally with preprocessing.

    ``preprocess`` modes:
      - ``"none"``: raw image, no enhancement
      - ``"full"``: grayscale + CLAHE + binarize + upscale (best for grid cells)
      - ``"gray"``: grayscale + upscale only (best for summary area with
        colored text that binarization would destroy)
    """
    engine = get_ocr_engine()

    if preprocess == "full":
        target_path = preprocess_for_ocr(image_path)
    elif preprocess == "gray":
        target_path = preprocess_grayscale_only(image_path)
    else:
        target_path = image_path

    try:
        raw_result = engine(str(target_path))
    finally:
        if preprocess != "none" and target_path != image_path:
            try:
                target_path.unlink(missing_ok=True)
            except Exception:
                pass

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
        if text.strip() and score >= min_confidence:
            lines.append(OcrLine(text=text.strip(), score=score))
    return lines


def extract_codes(lines: Iterable[OcrLine]) -> list[str]:
    """Extract bead color codes from OCR lines.

    Uses CODE_PATTERN (letter + 1-2 digits) which naturally filters
    out pure-number axis coordinates, garbled text, and non-code content.
    """
    codes: list[str] = []
    for line in lines:
        codes.extend(_extract_normalized_codes(line.text))
    return codes


# Keywords that indicate a total/summary line (not per-color counts)
_TOTAL_KEYWORDS = ["所需", "豆子", "数量", "total", "sum", "合计", "总计", "共需"]


def _is_total_line(text: str) -> bool:
    """Check if a text line is a total/summary rather than a code-count pair."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in _TOTAL_KEYWORDS)


def extract_count_pairs(lines: Iterable[OcrLine]) -> dict[str, int]:
    """Extract code→count pairs from OCR lines.

    Handles two common summary-area layouts:
      1. Same-line:  "B3 42" or "B3:42"
      2. Separate-line: codes and counts on different lines
    """
    counts: dict[str, int] = {}

    # Strategy 1: same-line pairs (join all text first)
    all_text = " ".join(line.text for line in lines)
    pairs_found = RAW_PAIR_PATTERN.findall(all_text.upper())
    # Only trust same-line strategy if it finds multiple pairs
    # (a single pair could be a spurious match from concatenated lines)
    if len(pairs_found) >= 3:
        for code, value in pairs_found:
            normalized = _normalize_code_token(code)
            if normalized:
                counts[normalized] = int(value)
        return counts

    # Strategy 2: codes and counts on separate lines
    # Collect codes and numbers in order, then pair them up
    text_lines = [line.text for line in lines]
    codes_seen: list[str] = []
    nums_seen: list[int] = []

    for text in text_lines:
        # Skip total/summary lines (they contain numbers but are not per-color counts)
        if _is_total_line(text):
            continue

        code_matches = _extract_normalized_codes(text)
        num_matches = NUMBER_PATTERN.findall(text)
        pair_matches = RAW_PAIR_PATTERN.findall(text.upper())

        if pair_matches:
            # This line contains code+count pairs — use them directly
            for code, value in pair_matches:
                normalized = _normalize_code_token(code)
                if normalized:
                    counts.setdefault(normalized, int(value))
        elif code_matches and not num_matches:
            codes_seen.extend(code_matches)
        elif num_matches and not code_matches:
            nums_seen.extend(int(v) for v in num_matches)
        # else: mixed content without clear pairs — skip

    # Pair codes with numbers in order
    if codes_seen and nums_seen and not counts:
        for i, code in enumerate(codes_seen):
            if i < len(nums_seen):
                counts[code] = nums_seen[i]

    return counts


def extract_axis_numbers(lines: Iterable[OcrLine]) -> int:
    numbers: list[int] = []
    for line in lines:
        numbers.extend(int(value) for value in NUMBER_PATTERN.findall(line.text))
    return max(numbers) if numbers else 0
