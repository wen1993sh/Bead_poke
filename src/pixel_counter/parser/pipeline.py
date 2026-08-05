from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from urllib.parse import quote

from PIL import Image

from pixel_counter.config import OUTPUT_DIR, TemplatePreset, ensure_output_dir, load_template_presets
from pixel_counter.models import BeadCount, ParseResult
from pixel_counter.parser.json_writer import write_index, write_parse_result, write_review_report
from pixel_counter.parser.layout_locator import locate_layout
from pixel_counter.parser.ocr import (
    crop_to_temp_file,
    extract_axis_numbers,
    extract_codes,
    extract_count_pairs,
    recognize_lines,
)
from pixel_counter.parser.reconciler import reconcile_counts
from pixel_counter.parser.scanner import scan_image_files
from pixel_counter.parser.template_detector import detect_template
from pixel_counter.shared.summarize import merge_beads, total_beads


def _center_crop_for_box(image_path: Path, box: tuple[int, int, int, int]) -> Path:
    return crop_to_temp_file(image_path, box)


def infer_name_from_path(image_path: Path) -> str:
    raw = image_path.stem
    if raw.isdigit():
        return raw
    return raw


def parse_image(image_path: Path, presets: list[TemplatePreset] | None = None) -> ParseResult:
    presets = presets or load_template_presets()
    template_match = detect_template(image_path, presets)
    layout = locate_layout(image_path, template_match.preset)

    warnings: list[str] = []

    grid_crop = _center_crop_for_box(image_path, layout.grid_box)
    summary_crop = _center_crop_for_box(image_path, layout.summary_box)
    axis_top_crop = _center_crop_for_box(image_path, layout.axis_top_box)

    try:
        grid_lines = recognize_lines(grid_crop, preprocess="full")
    except Exception as exc:
        warnings.append(f"grid-ocr-failed: {exc}")
        grid_lines = []

    try:
        summary_lines = recognize_lines(summary_crop, preprocess="none")
    except Exception as exc:
        warnings.append(f"summary-ocr-failed: {exc}")
        summary_lines = []

    try:
        axis_lines = recognize_lines(axis_top_crop, preprocess="full")
    except Exception as exc:
        warnings.append(f"axis-ocr-failed: {exc}")
        axis_lines = []

    grid_counts = Counter(extract_codes(grid_lines))
    summary_counts = extract_count_pairs(summary_lines)
    grid_rows = template_match.rows or extract_axis_numbers(axis_lines)
    grid_cols = template_match.cols or extract_axis_numbers(axis_lines)

    status, diffs = reconcile_counts(dict(grid_counts), summary_counts)
    if not grid_counts:
        warnings.append("grid-codes-empty")
        status = "error"

    merged_beads = merge_beads(BeadCount(code=code, count=count) for code, count in grid_counts.items())
    total = total_beads(merged_beads)

    # Confidence: based on code-set overlap between grid and summary
    if not grid_counts:
        confidence = 0.0
    elif not summary_counts:
        confidence = 0.60
    else:
        overlap = set(summary_counts) & set(grid_counts)
        all_summary = set(summary_counts)
        if all_summary:
            confidence = 0.70 + 0.25 * (len(overlap) / len(all_summary))
        else:
            confidence = 0.60

    return ParseResult(
        id=image_path.stem,
        name=infer_name_from_path(image_path),
        image=str(image_path.as_posix()),
        template=template_match.template_id,
        grid_rows=grid_rows,
        grid_cols=grid_cols,
        beads=merged_beads,
        total=total,
        confidence=confidence,
        status=status,
        warnings=warnings,
        reviewed=False,
        reviewed_by=None,
        reviewed_at=None,
        diffs=diffs,
        source_version="0.1.0",
    )


def build_catalog(image_dir: Path, output_dir: Path | None = None) -> dict:
    ensure_output_dir()
    output_dir = output_dir or OUTPUT_DIR
    presets = load_template_presets()
    items: list[dict] = []

    for image_path in scan_image_files(image_dir):
        result = parse_image(image_path, presets)
        item_path = output_dir / f"{image_path.stem}.json"
        write_parse_result(item_path, result)

        if result.status == "review":
            review_path = output_dir / "reviews" / f"{image_path.stem}.json"
            write_review_report(review_path, result.to_dict())

        items.append(
            {
                "id": result.id,
                "name": result.name,
                "image": f"/images/{quote(image_path.name)}",
                "template": result.template,
                "grid_rows": result.grid_rows,
                "grid_cols": result.grid_cols,
                "total": result.total,
                "status": result.status,
                "confidence": result.confidence,
                "warnings": result.warnings,
                "beads": [{"code": b.code, "count": b.count} for b in result.beads],
            }
        )

    index_path = output_dir / "index.json"
    write_index(index_path, items)
    return {"index": str(index_path), "items": items}


def load_index(index_path: Path) -> dict:
    if not index_path.exists():
        return {"items": [], "total_items": 0}
    return json.loads(index_path.read_text(encoding="utf-8"))
