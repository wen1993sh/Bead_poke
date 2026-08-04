from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from pixel_counter.config import IMAGE_DIR, INDEX_FILE, OUTPUT_DIR
from pixel_counter.parser.pipeline import build_catalog, load_index


def build_app() -> FastAPI:
    app = FastAPI(title="Pixel Bead Counter")
    static_dir = Path(__file__).resolve().parent.parent / "web" / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def home() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/api/index")
    def get_index() -> JSONResponse:
        return JSONResponse(load_index(INDEX_FILE))

    @app.post("/api/rebuild")
    def rebuild() -> JSONResponse:
        payload = build_catalog(IMAGE_DIR, OUTPUT_DIR)
        return JSONResponse(payload)

    return app
