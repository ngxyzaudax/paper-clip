from common.format_spec import FLAG_QR_SCALE_MASK, FLAG_QR_SCALE_SHIFT, QR_SCALE_MM


def qr_scale_index(module_mm: float) -> int:
    nearest = min(range(len(QR_SCALE_MM)), key=lambda index: abs(QR_SCALE_MM[index] - module_mm))
    if abs(QR_SCALE_MM[nearest] - float(module_mm)) > 0.005:
        raise ValueError(f"QR module {module_mm:g} mm is not a supported scale")
    return nearest


def qr_mm_from_flags(flags: int) -> float:
    index = (int(flags) >> FLAG_QR_SCALE_SHIFT) & 0x7
    return QR_SCALE_MM[index]


def flags_with_qr_mm(flags: int, module_mm: float) -> int:
    index = qr_scale_index(module_mm)
    cleared = int(flags) & ~FLAG_QR_SCALE_MASK
    return cleared | (index << FLAG_QR_SCALE_SHIFT)
