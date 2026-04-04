from pathlib import Path

import cv2
import numpy as np

SUPPORTED_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp")


def is_image_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTS


def load_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    return image


def resolve_input_images(input_path: Path) -> list[Path]:
    if is_image_file(input_path):
        return [input_path]
    if input_path.is_dir():
        image_files: list[Path] = []
        for ext in SUPPORTED_IMAGE_EXTS:
            image_files.extend(input_path.glob(f"*{ext}"))
        image_files = sorted(image_files)
        if not image_files:
            raise FileNotFoundError(f"No image files found in {input_path}")
        return image_files
    raise ValueError(f"Unsupported input: {input_path} (expected image file or directory)")
