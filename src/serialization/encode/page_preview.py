from PIL import Image

from common.config import PaperClipConfig
from common.page_layout import data_capacity_bytes, grid_dimensions, valid_cells_ordered
from common.symbols import bytes_to_symbols
from common.types import SymbolGrid
from serialization.encode.encoder import _sparse_symbol_grid, compute_total_pages
from serialization.encode.frame_payload import PreparedPayload
from serialization.encode.parity_render import render_parity_pages
from serialization.encode.renderer import render_page
from serialization.encode.stripe import mark_unused


def layout_page(config: PaperClipConfig) -> Image.Image:
    cols, rows = grid_dimensions(config)
    valid = valid_cells_ordered(config)
    grid: SymbolGrid = [[-1] * cols for _ in range(rows)]
    prepared = PreparedPayload(b"", bytes(32), 0, 0)
    return render_page(mark_unused(grid, valid), 0, 1, 1, prepared, config)


def payload_page(prepared: PreparedPayload, config: PaperClipConfig, index: int) -> Image.Image:
    data_pages = compute_total_pages(len(prepared.payload), config)
    total_pages = data_pages + config.redundancy_pages
    if index < 0 or index >= total_pages:
        raise ValueError(f"page {index} is outside 0..{total_pages - 1}")
    if index < data_pages:
        return _data_page(prepared, config, index, data_pages, total_pages)
    parity = render_parity_pages(prepared.payload, config, data_pages, total_pages, prepared, None)
    return parity[index - data_pages]


def _data_page(
    prepared: PreparedPayload,
    config: PaperClipConfig,
    index: int,
    data_pages: int,
    total_pages: int,
) -> Image.Image:
    cols, rows = grid_dimensions(config)
    valid = valid_cells_ordered(config)
    cap = data_capacity_bytes(config)
    chunk = prepared.payload[index * cap:(index + 1) * cap]
    symbols = bytes_to_symbols(chunk, config.num_symbols)
    grid = _sparse_symbol_grid(symbols, cols, rows, valid)
    return render_page(grid, index, total_pages, data_pages, prepared, config)
