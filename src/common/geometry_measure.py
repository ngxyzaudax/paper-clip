def quantize_mm(mm: float) -> float:
    return round(float(mm) * 100.0) / 100.0


def mm_to_hundredths(mm: float) -> int:
    return int(round(quantize_mm(mm) * 100.0))


def hundredths_to_mm(value: int) -> float:
    return int(value) / 100.0


def mm_to_px(mm: float, dpi: int) -> int:
    return int(round(float(mm) * dpi / 25.4))


def snap_up(px: int, cell: int) -> int:
    if px <= 0:
        return 0
    return ((px + cell - 1) // cell) * cell


def snap_down(px: int, cell: int) -> int:
    return max(0, (px // cell) * cell)


def margin_px(mm: float, dpi: int, cell: int) -> int:
    return snap_up(mm_to_px(mm, dpi), cell)
