from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from fastapi import FastAPI
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from pixel_counter.config import IMAGE_DIR, INDEX_FILE, OUTPUT_DIR
from pixel_counter.parser.pipeline import build_catalog, load_index


COLOR_LIBRARY_FILE = OUTPUT_DIR / "color_library.json"


class ReviewBeadItem(BaseModel):
    code: str
    count: int = Field(ge=0)


class ReviewSavePayload(BaseModel):
    beads: list[ReviewBeadItem]
    reviewer: str | None = None
    status: str | None = None


class ColorLibraryUpdatePayload(BaseModel):
    codes: dict[str, str]


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _item_file(item_id: str) -> Path:
    return OUTPUT_DIR / f"{item_id}.json"


def _resolve_item_file(item_id: str) -> Path | None:
    direct_path = _item_file(item_id)
    if direct_path.exists():
        return direct_path

    # Some historical files may have non-matching stems due to filename encoding issues.
    for json_path in OUTPUT_DIR.glob("*.json"):
        if json_path.name in {"index.json", "color_library.json"}:
            continue
        payload = _read_json(json_path, {})
        payload_id = str(payload.get("id", "")).strip()
        payload_name = str(payload.get("name", "")).strip()
        if item_id == payload_id or item_id == payload_name:
            return json_path
    return None


def _normalize_beads(beads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for bead in beads:
        code = str(bead.get("code", "")).strip().upper()
        if not code:
            continue
        try:
            count = int(bead.get("count", 0))
        except Exception:
            continue
        if count < 0:
            continue
        normalized.append({"code": code, "count": count})
    normalized.sort(key=lambda item: item["code"])
    return normalized


def _total_from_beads(beads: list[dict[str, Any]]) -> int:
    return sum(int(item.get("count", 0)) for item in beads)


def _public_image_path(raw_path: str | None) -> str:
    if not raw_path:
        return ""
    path = Path(str(raw_path))
    return f"/images/{path.name}"


def _save_index(payload: dict[str, Any]) -> None:
    payload["total_items"] = len(payload.get("items", []))
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    _write_json(INDEX_FILE, payload)


def _update_index_item(item_payload: dict[str, Any]) -> None:
    index_payload = load_index(INDEX_FILE)
    items = index_payload.get("items", [])
    item_id = str(item_payload.get("id", ""))
    updated = False
    for entry in items:
        if str(entry.get("id", "")) == item_id:
            entry["id"] = item_payload.get("id")
            entry["name"] = item_payload.get("name")
            entry["image"] = _public_image_path(item_payload.get("image"))
            entry["template"] = item_payload.get("template")
            entry["grid_rows"] = item_payload.get("grid_rows")
            entry["grid_cols"] = item_payload.get("grid_cols")
            entry["total"] = item_payload.get("total")
            entry["status"] = item_payload.get("status")
            entry["confidence"] = item_payload.get("confidence")
            entry["warnings"] = item_payload.get("warnings", [])
            entry["beads"] = item_payload.get("beads", [])
            entry["reviewed"] = item_payload.get("reviewed", False)
            entry["reviewed_at"] = item_payload.get("reviewed_at")
            updated = True
            break
    if not updated:
        items.append(
            {
                "id": item_payload.get("id"),
                "name": item_payload.get("name"),
                "image": _public_image_path(item_payload.get("image")),
                "template": item_payload.get("template"),
                "grid_rows": item_payload.get("grid_rows"),
                "grid_cols": item_payload.get("grid_cols"),
                "total": item_payload.get("total"),
                "status": item_payload.get("status"),
                "confidence": item_payload.get("confidence"),
                "warnings": item_payload.get("warnings", []),
                "beads": item_payload.get("beads", []),
                "reviewed": item_payload.get("reviewed", False),
                "reviewed_at": item_payload.get("reviewed_at"),
            }
        )

    index_payload["items"] = items
    _save_index(index_payload)


def _extract_palette_from_image(image_path: Path, max_colors: int = 8) -> list[tuple[str, int]]:
    if not image_path.exists():
        return []
    with Image.open(image_path) as image:
        image = image.convert("RGB").resize((200, 200))
        quantized = image.quantize(colors=max_colors)
        raw_colors = quantized.getcolors(max_colors * 4) or []
        palette = quantized.getpalette() or []

    result: list[tuple[str, int]] = []
    for count, color_index in raw_colors:
        start = color_index * 3
        if start + 2 >= len(palette):
            continue
        r, g, b = palette[start], palette[start + 1], palette[start + 2]
        result.append((f"#{r:02x}{g:02x}{b:02x}", int(count)))
    return result


def _build_color_library_from_images(index_payload: dict[str, Any]) -> dict[str, Any]:
    items = index_payload.get("items", [])
    color_counts: dict[str, int] = {}
    code_set: set[str] = set()

    for item in items:
        image_ref = str(item.get("image", ""))
        image_name = Path(unquote(image_ref)).name
        image_path = IMAGE_DIR / image_name
        for color_hex, count in _extract_palette_from_image(image_path):
            color_counts[color_hex] = color_counts.get(color_hex, 0) + count
        for bead in item.get("beads", []):
            code = str(bead.get("code", "")).strip().upper()
            if code:
                code_set.add(code)

    sorted_palette = sorted(color_counts.items(), key=lambda item: item[1], reverse=True)
    if not sorted_palette:
        sorted_palette = [("#b0bec5", 1), ("#90a4ae", 1), ("#78909c", 1), ("#607d8b", 1)]

    palette_entries = [
        {"hex": color_hex, "weight": weight}
        for color_hex, weight in sorted_palette[:24]
    ]
    palette_hex = [entry["hex"] for entry in palette_entries]

    codes = {}
    for code in sorted(code_set):
        hash_value = int(hashlib.sha1(code.encode("utf-8")).hexdigest(), 16)
        color_hex = palette_hex[hash_value % len(palette_hex)]
        codes[code] = color_hex

    return {
        "source": "image-dominant-palette",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "palette": palette_entries,
        "codes": codes,
    }


def _load_color_library() -> dict[str, Any]:
    if COLOR_LIBRARY_FILE.exists():
        return _read_json(COLOR_LIBRARY_FILE, {})
    index_payload = load_index(INDEX_FILE)
    library = _build_color_library_from_images(index_payload)
    _write_json(COLOR_LIBRARY_FILE, library)
    return library


def build_app() -> FastAPI:
    app = FastAPI(title="Pixel Bead Counter")
    static_dir = Path(__file__).resolve().parent.parent / "web" / "static"
    image_dir = Path(__file__).resolve().parents[3] / "image"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    if image_dir.exists():
        app.mount("/images", StaticFiles(directory=image_dir), name="images")

    @app.get("/")
    def home() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/api/index")
    def get_index() -> JSONResponse:
        return JSONResponse(load_index(INDEX_FILE))

    @app.get("/api/items/{item_id}")
    def get_item(item_id: str) -> JSONResponse:
        item_path = _resolve_item_file(item_id)
        if not item_path:
            return JSONResponse({"error": "not-found", "id": item_id}, status_code=404)
        payload = _read_json(item_path, {})
        payload["image"] = _public_image_path(payload.get("image"))
        return JSONResponse(payload)

    @app.post("/api/items/{item_id}/review")
    def save_item_review(item_id: str, body: ReviewSavePayload) -> JSONResponse:
        item_path = _resolve_item_file(item_id)
        if not item_path:
            return JSONResponse({"error": "not-found", "id": item_id}, status_code=404)

        payload = _read_json(item_path, {})
        beads = _normalize_beads([{"code": row.code, "count": row.count} for row in body.beads])
        payload["beads"] = beads
        payload["total"] = _total_from_beads(beads)
        payload["reviewed"] = True
        payload["reviewed_by"] = body.reviewer or "web"
        payload["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        payload["status"] = body.status if body.status in {"ok", "review", "error"} else "ok"
        if payload["status"] == "ok":
            payload["diffs"] = []
            payload["warnings"] = ["manual-reviewed"]

        _write_json(item_path, payload)
        _update_index_item(payload)

        review_path = OUTPUT_DIR / "reviews" / f"{item_id}.json"
        if payload["status"] == "review":
            _write_json(review_path, payload)
        elif review_path.exists():
            review_path.unlink()

        output_payload = dict(payload)
        output_payload["image"] = _public_image_path(payload.get("image"))
        return JSONResponse(output_payload)

    @app.get("/api/color-library")
    def get_color_library() -> JSONResponse:
        return JSONResponse(_load_color_library())

    @app.post("/api/color-library/rebuild")
    def rebuild_color_library() -> JSONResponse:
        index_payload = load_index(INDEX_FILE)
        library = _build_color_library_from_images(index_payload)
        _write_json(COLOR_LIBRARY_FILE, library)
        return JSONResponse(library)

    @app.post("/api/color-library/update")
    def update_color_library(body: ColorLibraryUpdatePayload) -> JSONResponse:
        library = _load_color_library()
        existing_codes = library.get("codes", {})
        for code, color_hex in body.codes.items():
            clean_code = str(code).strip().upper()
            clean_color = str(color_hex).strip().lower()
            if clean_code and clean_color:
                existing_codes[clean_code] = clean_color
        library["codes"] = existing_codes
        library["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_json(COLOR_LIBRARY_FILE, library)
        return JSONResponse(library)

    @app.post("/api/rebuild")
    def rebuild() -> JSONResponse:
        payload = build_catalog(IMAGE_DIR, OUTPUT_DIR)
        return JSONResponse(payload)

    return app
