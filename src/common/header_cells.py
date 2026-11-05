from functools import lru_cache

from common.config import PaperClipConfig
from common.geometry import page_geometry
from common.header_grid import header_grid_symbols
from common.valid_cells import valid_cells_row_major


def split_cells(config: PaperClipConfig) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    header, data = _cached_split(config)
    return list(header), list(data)


@lru_cache(maxsize=64)
def _cached_split(
    config: PaperClipConfig,
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    geometry = page_geometry(config)
    cells = valid_cells_row_major(geometry.cols, geometry.rows, geometry.cell, list(geometry.forbidden))
    need = header_grid_symbols(config.num_symbols)
    if len(cells) <= need:
        raise ValueError("page is too small for the in-grid header")
    stride = len(cells) // need
    header = tuple(cells[index * stride] for index in range(need))
    taken = set(header)
    data = tuple(cell for cell in cells if cell not in taken)
    return header, data
