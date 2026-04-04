import logging
from pathlib import Path

logger = logging.getLogger(__name__)

STANDARD_DPIS = (150, 300, 600, 720, 1200, 1440, 2400, 2880, 4800, 5760)


def snap_to_standard_dpi(raw_dpi: float) -> int:
    for std in STANDARD_DPIS:
        if abs(raw_dpi - std) <= 2:
            return std
    return round(raw_dpi)


def read_png_dpi(file_path: Path) -> int | None:
    try:
        from PIL import Image
        img = Image.open(file_path)
        dpi_info = img.info.get("dpi")
        if dpi_info and dpi_info[0] > 0:
            return snap_to_standard_dpi(float(dpi_info[0]))
    except Exception:
        pass
    return None
