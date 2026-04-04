import math

from common.config import (
    CALIBRATION_BAR_ROWS,
    FINDER_PATTERN_MODULES,
    PaperClipConfig,
    TIMING_TRACK_WIDTH,
    palette_qr_image_size_px,
    qr_image_size_px,
)
from common.symbols import chunk_params, symbol_count
from common.types import Region


def mm_to_px(mm: float, dpi: int) -> int:
    return int(mm * dpi / 25.4)


def usable_area_px(config: PaperClipConfig) -> tuple[int, int]:
    total_w = mm_to_px(config.page_width_mm, config.scan_dpi)
    total_h = mm_to_px(config.page_height_mm, config.scan_dpi)
    margin = mm_to_px(config.margin_mm, config.scan_dpi)
    return total_w - 2 * margin, total_h - 2 * margin


def finder_pattern_size(config: PaperClipConfig) -> int:
    return FINDER_PATTERN_MODULES * config.cell_size_px


def metadata_band_height(config: PaperClipConfig) -> int:
    fp = finder_pattern_size(config)
    qr = qr_image_size_px()
    return max(fp, qr)


def qr_region(config: PaperClipConfig) -> Region:
    fp = finder_pattern_size(config)
    qr = qr_image_size_px()
    return Region(fp, 0, qr, qr)


def palette_qr_region(config: PaperClipConfig) -> Region:
    num_cal = len(config.calibrated_colors)
    if num_cal <= 0:
        qr_reg = qr_region(config)
        return Region(qr_reg.x + qr_reg.width, 0, 0, 0)
    qr_reg = qr_region(config)
    size = palette_qr_image_size_px(num_cal)
    return Region(qr_reg.x + qr_reg.width, 0, size, size)


def _palette_qr_shift(config: PaperClipConfig) -> int:
    pqr = palette_qr_region(config)
    if pqr.width == 0:
        return 0
    return pqr.width + config.cell_size_px


def calibration_region(config: PaperClipConfig) -> Region:
    qr_reg = qr_region(config)
    cell = config.cell_size_px
    total_symbols = symbol_count(config.num_colors)
    cal_width = total_symbols * cell
    cal_height = CALIBRATION_BAR_ROWS * cell
    x = qr_reg.x + qr_reg.width + _palette_qr_shift(config)
    return Region(x, 0, cal_width, cal_height)


def rainbow_region(config: PaperClipConfig) -> Region:
    cal = calibration_region(config)
    usable_w, _ = usable_area_px(config)
    fp = finder_pattern_size(config)
    gap = config.cell_size_px
    x = cal.x + cal.width + gap
    width = usable_w - x - fp - gap
    return Region(x, 0, max(0, width), cal.height)


def info_region(config: PaperClipConfig) -> Region:
    cal = calibration_region(config)
    usable_w, _ = usable_area_px(config)
    fp = finder_pattern_size(config)
    x = cal.x
    y = cal.y + cal.height
    width = usable_w - x - fp
    height = metadata_band_height(config) - cal.height
    return Region(x, y, width, height)


def data_grid_region(config: PaperClipConfig) -> Region:
    usable_w, usable_h = usable_area_px(config)
    band_h = metadata_band_height(config)
    fp_size = finder_pattern_size(config)
    y_start = band_h + TIMING_TRACK_WIDTH * config.cell_size_px
    x_start = TIMING_TRACK_WIDTH * config.cell_size_px
    available_w = usable_w - x_start
    available_h = usable_h - y_start - fp_size
    grid_w = (available_w // config.cell_size_px) * config.cell_size_px
    grid_h = (available_h // config.cell_size_px) * config.cell_size_px
    return Region(x_start, y_start, grid_w, grid_h)


def grid_dimensions(config: PaperClipConfig) -> tuple[int, int]:
    region = data_grid_region(config)
    cols = region.width // config.cell_size_px
    rows = region.height // config.cell_size_px
    return cols, rows


def data_capacity_symbols(config: PaperClipConfig) -> int:
    cols, rows = grid_dimensions(config)
    return cols * rows


def data_capacity_bytes(config: PaperClipConfig) -> int:
    from common.codec import calculate_ecc_symbols, effective_block_size
    from common.config import BLOCK_SIZE, PAYLOAD_HEADER_REDUNDANCY, PAYLOAD_HEADER_STRUCT

    total_cells = data_capacity_symbols(config)
    n = symbol_count(config.num_colors)
    k, m = chunk_params(n)
    raw_bytes = (total_cells // m) * k
    payload_overhead = PAYLOAD_HEADER_STRUCT.size * PAYLOAD_HEADER_REDUNDANCY
    available = raw_bytes - payload_overhead
    if available <= 0:
        return 0
    ecc_symbols = calculate_ecc_symbols(BLOCK_SIZE, config.rs_redundancy)
    bs = effective_block_size(ecc_symbols)
    encoded_block = bs + ecc_symbols
    num_blocks = available // encoded_block
    return num_blocks * bs


def pages_needed(data_size: int, config: PaperClipConfig) -> int:
    capacity = data_capacity_bytes(config)
    if capacity <= 0:
        raise ValueError("Page capacity is zero with current config")
    return math.ceil(data_size / capacity)


def page_image_size(config: PaperClipConfig) -> tuple[int, int]:
    width = mm_to_px(config.page_width_mm, config.scan_dpi)
    height = mm_to_px(config.page_height_mm, config.scan_dpi)
    return width, height


def margin_offset(config: PaperClipConfig) -> tuple[int, int]:
    m = mm_to_px(config.margin_mm, config.scan_dpi)
    return m, m
