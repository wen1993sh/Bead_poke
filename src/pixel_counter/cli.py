from __future__ import annotations

import argparse
from pathlib import Path

from pixel_counter.config import IMAGE_DIR, INDEX_FILE, OUTPUT_DIR
from pixel_counter.parser.pipeline import build_catalog, load_index
from pixel_counter.viewer.app import build_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pixel-counter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_command = subparsers.add_parser("parse-images", help="Parse images into JSON files")
    parse_command.add_argument("--image-dir", type=Path, default=IMAGE_DIR)
    parse_command.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)

    index_command = subparsers.add_parser("build-index", help="Print the current index file")
    index_command.add_argument("--index-file", type=Path, default=INDEX_FILE)

    serve_command = subparsers.add_parser("serve", help="Run the FastAPI viewer")
    serve_command.add_argument("--host", default="127.0.0.1")
    serve_command.add_argument("--port", type=int, default=8000)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "parse-images":
        payload = build_catalog(args.image_dir, args.output_dir)
        print(payload["index"])
        return

    if args.command == "build-index":
        print(load_index(args.index_file))
        return

    if args.command == "serve":
        import uvicorn

        app = build_app()
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
