from typing import NamedTuple

TAG_HOLD_MM = 4.0
TAG_FAIL_MM = 3.0
CELL_HOLD_PX = 22
CELL_TAG_DROP_PX = 18
SYMBOLS_HOLD = 5
SYMBOLS_EDGE = 11
QR_MODULE_HOLD_MM = 0.36
PITCH_HOLD_MM = 16.0
PRESET_DPI = 720


class DensityPreset(NamedTuple):
    cell_size_px: int
    num_symbols: int
    tag_size_mm: float
    tag_pitch_mm: float
    print_dpi: int
    qr_module_mm: float


def et8500_preset() -> DensityPreset:
    return DensityPreset(
        CELL_HOLD_PX,
        SYMBOLS_HOLD,
        TAG_HOLD_MM,
        PITCH_HOLD_MM,
        PRESET_DPI,
        QR_MODULE_HOLD_MM,
    )
