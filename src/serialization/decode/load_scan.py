from collections.abc import Sequence
from pathlib import Path

import numpy as np
from PIL import Image

from serialization.decode.errors import DecodeError

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def load_scans(source: Path | Sequence[np.ndarray] | np.ndarray) -> list[np.ndarray]:
    if isinstance(source, np.ndarray):
        return [_as_rgb(source)]
    if isinstance(source, Sequence) and not isinstance(source, (str, Path)):
        if not source:
            raise DecodeError("no scan images were provided")
        return [_as_rgb(np.asarray(item)) for item in source]
    path = Path(source)
    paths = _image_paths(path)
    return [_load_file(item) for item in paths]


def _image_paths(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    if not source.exists():
        raise DecodeError(f"scan source does not exist: {source}")
    folder = source / "scans" if (source / "scans").is_dir() else source
    paths = [item for item in sorted(folder.iterdir()) if item.suffix.lower() in _IMAGE_SUFFIXES]
    if not paths:
        raise DecodeError(f"no scan images in {source}")
    return paths


def _load_file(path: Path) -> np.ndarray:
    image = Image.open(path)
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    else:
        image = image.convert("RGB")
    return _as_rgb(np.asarray(image))


def _as_rgb(image: np.ndarray) -> np.ndarray:
    if image.ndim != 3 or image.shape[2] < 3:
        raise DecodeError("scan image must be RGB")
    rgb = np.ascontiguousarray(image[:, :, :3])
    if rgb.dtype != np.uint8:
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    return rgb
