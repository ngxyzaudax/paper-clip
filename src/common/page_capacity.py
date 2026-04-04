import math

from common.codec import calculate_ecc_symbols, effective_block_size
from common.config import BLOCK_SIZE, PAYLOAD_HEADER_REDUNDANCY, PAYLOAD_HEADER_STRUCT, PaperClipConfig
from common.layout_metrics import layout_forbidden_rects, usable_area_px
from common.layout_spatial import count_valid_cells_row_major, valid_cells_row_major
from common.symbols import chunk_params, symbol_count


def grid_dimensions(config: PaperClipConfig) -> tuple[int, int]:
    uw, uh = usable_area_px(config)
    cell = config.cell_size_px
    cols = uw // cell
    rows = uh // cell
    return cols, rows


def data_capacity_symbols(config: PaperClipConfig) -> int:
    cols, rows = grid_dimensions(config)
    cell = config.cell_size_px
    return count_valid_cells_row_major(
        cols, rows, cell, layout_forbidden_rects(config),
    )


def valid_cells_ordered(config: PaperClipConfig) -> list[tuple[int, int]]:
    cols, rows = grid_dimensions(config)
    cell = config.cell_size_px
    return valid_cells_row_major(
        cols, rows, cell, layout_forbidden_rects(config),
    )


def data_capacity_bytes(config: PaperClipConfig) -> int:
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
