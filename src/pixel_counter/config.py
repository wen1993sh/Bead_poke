from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGE_DIR = PROJECT_ROOT / "image"
OUTPUT_DIR = PROJECT_ROOT / "output"
CONFIG_DIR = PROJECT_ROOT / "config"
TEMPLATE_PRESETS_FILE = CONFIG_DIR / "template_presets.json"
INDEX_FILE = OUTPUT_DIR / "index.json"


@dataclass(slots=True)
class TemplatePreset:
    id: str
    rows: int
    cols: int
    image_size: tuple[int, int] | None
    title_band: tuple[float, float, float, float]
    axis_top_band: tuple[float, float, float, float]
    grid_band: tuple[float, float, float, float]
    summary_band: tuple[float, float, float, float]
    notes: str = ""


def _as_box(value: Any, fallback: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    if isinstance(value, list) and len(value) == 4:
        return (float(value[0]), float(value[1]), float(value[2]), float(value[3]))
    return fallback


def load_template_presets(path: Path | None = None) -> list[TemplatePreset]:
    preset_path = path or TEMPLATE_PRESETS_FILE
    if not preset_path.exists():
        example_path = preset_path.with_name("template_presets.example.json")
        if example_path.exists():
            preset_path = example_path
    if not preset_path.exists():
        return []
    data = json.loads(preset_path.read_text(encoding="utf-8"))
    presets: list[TemplatePreset] = []
    for item in data.get("presets", []):
        presets.append(
            TemplatePreset(
                id=str(item.get("id", "default-grid")),
                rows=int(item.get("rows", 0)),
                cols=int(item.get("cols", 0)),
                image_size=(int(item["image_size"][0]), int(item["image_size"][1])) if item.get("image_size") else None,
                title_band=_as_box(item.get("title_band"), (0.0, 0.0, 1.0, 0.09)),
                axis_top_band=_as_box(item.get("axis_top_band"), (0.0, 0.09, 1.0, 0.14)),
                grid_band=_as_box(item.get("grid_band"), (0.03, 0.14, 0.97, 0.86)),
                summary_band=_as_box(item.get("summary_band"), (0.0, 0.86, 1.0, 1.0)),
                notes=str(item.get("notes", "")),
            )
        )
    return presets


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
