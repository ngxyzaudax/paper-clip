from common.format_spec import QR_MODULE_MM, qr_module_count
from common.geometry_measure import mm_to_px


def qr_module_px(dpi: int, module_mm: float = QR_MODULE_MM) -> int:
    return max(4, mm_to_px(module_mm, dpi))


def qr_side_px(dpi: int, module_mm: float = QR_MODULE_MM) -> int:
    return qr_module_count() * qr_module_px(dpi, module_mm)
