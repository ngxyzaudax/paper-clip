import hashlib
from io import BytesIO
from pathlib import Path

from PIL import Image

from common.data_store import DATA_ROOT

THUMB_SIZES = frozenset({320, 1600, 3200})


def thumb_root() -> Path:
    return DATA_ROOT / ".thumbs"


def sized_image(source: Path, size: int | None) -> Path:
    if size not in THUMB_SIZES:
        return source
    stat = source.stat()
    key = hashlib.sha256(f"{source.resolve()}|{stat.st_mtime_ns}|{stat.st_size}|{size}".encode()).hexdigest()
    dest = thumb_root() / f"{key}.jpg"
    if not dest.is_file():
        _write_thumb(source, dest, size)
    return dest


def _write_thumb(source: Path, dest: Path, size: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as opened:
        image = opened.convert("RGB")
    image.thumbnail((size, size), Image.Resampling.BOX)
    partial = dest.with_suffix(".part")
    image.save(partial, "JPEG", quality=82)
    partial.replace(dest)


def jpeg_bytes(image: Image.Image, long_side: int = 1400) -> bytes:
    copy = image.convert("RGB")
    copy.thumbnail((long_side, long_side), Image.Resampling.BOX)
    buffer = BytesIO()
    copy.save(buffer, "JPEG", quality=80)
    return buffer.getvalue()
