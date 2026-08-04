from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from pixel_counter.config import TemplatePreset


@dataclass(slots=True)
class LayoutSpec:
    image_box: tuple[int, int, int, int]
    title_box: tuple[int, int, int, int]
    axis_top_box: tuple[int, int, int, int]
    grid_box: tuple[int, int, int, int]
    summary_box: tuple[int, int, int, int]


def _scale_box(box: tuple[float, float, float, float], width: int, height: int) -> tuple[int, int, int, int]:
    left = int(box[0] * width)
    top = int(box[1] * height)
    right = int(box[2] * width)
    bottom = int(box[3] * height)
    return (left, top, right, bottom)


def locate_layout(image_path: Path, preset: TemplatePreset | None = None) -> LayoutSpec:
    with Image.open(image_path) as image:
        width, height = image.size

    if preset is None:
        preset = TemplatePreset(
            id="default-grid",
            rows=0,
            cols=0,
            image_size=None,
            title_band=(0.0, 0.0, 1.0, 0.09),
            axis_top_band=(0.0, 0.09, 1.0, 0.14),
            grid_band=(0.03, 0.14, 0.97, 0.86),
            summary_band=(0.0, 0.86, 1.0, 1.0),
        )

    return LayoutSpec(
        image_box=(0, 0, width, height),
        title_box=_scale_box(preset.title_band, width, height),
        axis_top_box=_scale_box(preset.axis_top_band, width, height),
        grid_box=_scale_box(preset.grid_band, width, height),
        summary_box=_scale_box(preset.summary_band, width, height),
    )


def crop_box(image_path: Path, box: tuple[int, int, int, int]) -> Path:
    raise NotImplementedError("Use the crop_box helper in ocr.py to avoid duplicate temp-file logic.")
