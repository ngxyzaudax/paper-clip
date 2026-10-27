from common.format_spec import QR_MODULE_MM, qr_module_count
from common.geometry_measure import mm_to_px


def qr_module_px(dpi: int) -> int:
    raw = max(4, mm_to_px(QR_MODULE_MM, dpi))
    if raw % 2:
        raw += 1
    return raw


def qr_side_px(dpi: int) -> int:
    return qr_module_count() * qr_module_px(dpi)
