from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def _imread_gray(path: Path) -> np.ndarray:
    """Read image as grayscale, handling Unicode paths on Windows."""
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
        if image is not None:
            return image
    except Exception:
        pass
    # Fallback via PIL
    pil_img = Image.open(path).convert("L")
    return np.array(pil_img)


def _imwrite(path: Path, image: np.ndarray) -> None:
    """Write image, handling Unicode paths on Windows."""
    success, buf = cv2.imencode(".png", image)
    if not success:
        raise OSError(f"Failed to encode image for {path}")
    buf.tofile(str(path))


def preprocess_for_ocr(
    image_path: Path,
    *,
    upscale: int = 2,
    clip_limit: float = 2.0,
    tile_grid_size: tuple[int, int] = (8, 8),
    block_size: int = 15,
    c_value: int = 4,
) -> Path:
    """Apply preprocessing pipeline to improve OCR accuracy.

    Steps:
      1. Convert to grayscale
      2. CLAHE contrast enhancement
      3. Adaptive threshold binarization (black text on white bg)
      4. Upscale (default 2x) for better small-text recognition
      5. Save result to a temporary PNG

    Returns the path to the preprocessed image file.
    """
    image = _imread_gray(image_path)

    # CLAHE – contrast limited adaptive histogram equalization
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    enhanced = clahe.apply(image)

    # Adaptive threshold – binarize while preserving local detail
    binary = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size,
        c_value,
    )

    # Denoise
    denoised = cv2.fastNlMeansDenoising(binary, None, h=10)

    # Upscale for better OCR on small text
    if upscale > 1:
        h, w = denoised.shape
        denoised = cv2.resize(
            denoised,
            (w * upscale, h * upscale),
            interpolation=cv2.INTER_CUBIC,
        )

    import tempfile

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    _imwrite(Path(handle.name), denoised)
    handle.close()
    return Path(handle.name)


def preprocess_grayscale_only(image_path: Path, *, upscale: int = 2) -> Path:
    """Lightweight preprocessing: grayscale + upscale only.

    Useful for the summary area where text layout matters more
    than pure contrast.
    """
    arr = _imread_gray(image_path)

    if upscale > 1:
        h, w = arr.shape
        arr = cv2.resize(
            arr,
            (w * upscale, h * upscale),
            interpolation=cv2.INTER_CUBIC,
        )

    import tempfile

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    _imwrite(Path(handle.name), arr)
    handle.close()
    return Path(handle.name)
