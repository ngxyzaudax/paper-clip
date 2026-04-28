import math
from functools import lru_cache

from common.config import PaperClipConfig
from common.layout_metrics import layout_forbidden_rects, usable_area_px
from common.layout_spatial import count_valid_cells_row_major, valid_cells_row_major
from common.symbols import chunk_params


def grid_dimensions(config: PaperClipConfig) -> tuple[int, int]:
    uw, uh = usable_area_px(config)
    cell = config.cell_size_px
    cols = uw // cell
    rows = uh // cell
    return cols, rows


@lru_cache(maxsize=128)
def data_capacity_symbols(config: PaperClipConfig) -> int:
    cols, rows = grid_dimensions(config)
    cell = config.cell_size_px
    return count_valid_cells_row_major(
        cols, rows, cell, layout_forbidden_rects(config),
    )


@lru_cache(maxsize=32)
def valid_cells_ordered(config: PaperClipConfig) -> list[tuple[int, int]]:
    cols, rows = grid_dimensions(config)
    cell = config.cell_size_px
    return valid_cells_row_major(
        cols, rows, cell, layout_forbidden_rects(config),
    )


def data_capacity_bytes(config: PaperClipConfig) -> int:
    total_cells = data_capacity_symbols(config)
    n = config.num_symbols
    k, m = chunk_params(n)
    grid_bytes = (total_cells // m) * k
    return max(0, grid_bytes)


def pages_needed(data_size: int, config: PaperClipConfig) -> int:
    capacity = data_capacity_bytes(config)
    if capacity <= 0:
        raise ValueError("Page capacity is zero with current config")
    return math.ceil(data_size / capacity)
