import threading
from collections import OrderedDict
from io import BytesIO
from pathlib import Path

from PIL import Image

MAX_CROP = 800
KEEP_RASTERS = 2
_lock = threading.Lock()
_rasters: OrderedDict[tuple[str, int], Image.Image] = OrderedDict()


def crop_jpeg(source: Path, x: int, y: int, w: int, h: int) -> bytes:
    image = _raster(source)
    left = min(max(0, x), image.width - 1)
    top = min(max(0, y), image.height - 1)
    right = min(image.width, left + max(1, min(w, MAX_CROP)))
    bottom = min(image.height, top + max(1, min(h, MAX_CROP)))
    buffer = BytesIO()
    image.crop((left, top, right, bottom)).save(buffer, "JPEG", quality=90)
    return buffer.getvalue()


def centered_crop_jpeg(source: Path, fx: float, fy: float, w: int, h: int) -> bytes:
    image = _raster(source)
    x = round(min(max(fx, 0.0), 1.0) * image.width - w / 2)
    y = round(min(max(fy, 0.0), 1.0) * image.height - h / 2)
    return crop_jpeg(source, max(0, x), max(0, y), w, h)


def _raster(source: Path) -> Image.Image:
    key = (str(source.resolve()), source.stat().st_mtime_ns)
    with _lock:
        cached = _rasters.get(key)
        if cached is not None:
            _rasters.move_to_end(key)
            return cached
    with Image.open(source) as opened:
        image = opened.convert("RGB")
    with _lock:
        _rasters[key] = image
        while len(_rasters) > KEEP_RASTERS:
            _rasters.popitem(last=False)
    return image
