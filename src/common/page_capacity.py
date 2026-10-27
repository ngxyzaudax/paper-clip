import math
from functools import lru_cache

from common.config import PaperClipConfig
from common.geometry import page_geometry
from common.valid_cells import count_valid_cells_row_major, valid_cells_row_major
from common.symbols import chunk_params


def grid_dimensions(config: PaperClipConfig) -> tuple[int, int]:
    geometry = page_geometry(config)
    return geometry.cols, geometry.rows


@lru_cache(maxsize=128)
def data_capacity_symbols(config: PaperClipConfig) -> int:
    geometry = page_geometry(config)
    return count_valid_cells_row_major(
        geometry.cols, geometry.rows, geometry.cell, list(geometry.forbidden),
    )


@lru_cache(maxsize=32)
def valid_cells_ordered(config: PaperClipConfig) -> list[tuple[int, int]]:
    geometry = page_geometry(config)
    return valid_cells_row_major(
        geometry.cols, geometry.rows, geometry.cell, list(geometry.forbidden),
    )


def data_capacity_bytes(config: PaperClipConfig) -> int:
    total_cells = data_capacity_symbols(config)
    k, m = chunk_params(config.num_symbols)
    if m <= 0:
        return 0
    return max(0, (total_cells // m) * k)


def pages_needed(data_size: int, config: PaperClipConfig) -> int:
    capacity = data_capacity_bytes(config)
    if capacity <= 0:
        raise ValueError("Page capacity is zero with current config")
    return math.ceil(data_size / capacity)
