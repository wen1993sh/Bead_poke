from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from pixel_counter.config import TemplatePreset


@dataclass(slots=True)
class TemplateMatch:
    template_id: str
    rows: int
    cols: int
    confidence: float
    preset: TemplatePreset | None = None


def detect_template(image_path: Path, presets: list[TemplatePreset]) -> TemplateMatch:
    with Image.open(image_path) as image:
        width, height = image.size

    if not presets:
        return TemplateMatch(template_id="unknown", rows=0, cols=0, confidence=0.0)

    best_preset = None
    best_score = -1.0
    for preset in presets:
        score = 0.0
        if preset.image_size is not None:
            if preset.image_size == (width, height):
                score += 2.0
            else:
                dw = abs(preset.image_size[0] - width)
                dh = abs(preset.image_size[1] - height)
                score += max(0.0, 1.0 - ((dw + dh) / max(width + height, 1)))
        if preset.rows > 0 and preset.cols > 0:
            score += 0.2
        # Very light heuristic: presets are manually tuned per family.
        if preset.grid_band[3] - preset.grid_band[1] > 0.5:
            score += 0.1
        if width > 0 and height > 0:
            score += 0.1
        if score > best_score:
            best_score = score
            best_preset = preset

    if best_preset is None:
        return TemplateMatch(template_id="unknown", rows=0, cols=0, confidence=0.0)

    return TemplateMatch(
        template_id=best_preset.id,
        rows=best_preset.rows,
        cols=best_preset.cols,
        confidence=min(1.0, 0.5 + best_score),
        preset=best_preset,
    )
