from collections.abc import Callable
from pathlib import Path

from PIL import Image

from common.config import PaperClipConfig
from common.page_layout import data_capacity_bytes, grid_dimensions, valid_cells_ordered
from common.symbols import bytes_to_symbols
from serialization.encode.encoder import _sparse_symbol_grid
from serialization.encode.renderer import render_page

OnPageComplete = Callable[[int, int, Path | None], None]


def extract_page_payloads(
    payload: bytes, config: PaperClipConfig, data_pages: int,
) -> list[bytes]:
    from common.symbols import chunk_params, symbol_count
    from common.symbols import symbols_to_bytes as syms_to_raw

    cap = data_capacity_bytes(config)
    k, m = chunk_params(symbol_count(config.num_colors))
    page_payloads: list[bytes] = []
    for page in range(data_pages):
        chunk = payload[page * cap : (page + 1) * cap]
        syms = bytes_to_symbols(chunk, config.num_colors)
        page_payloads.append(syms_to_raw(syms, config.num_colors, (len(syms) // m) * k))
    return page_payloads


def render_parity_pages(
    payload: bytes, config: PaperClipConfig, data_pages: int, total_pages: int,
    sha256_hash: bytes, file_size: int, flags: int,
    on_page_complete: OnPageComplete | None,
) -> list[Image.Image]:
    from common.fountain import encode_parity_pages

    cols, rows = grid_dimensions(config)
    valid_order = valid_cells_ordered(config)
    data_page_payloads = extract_page_payloads(payload, config, data_pages)
    parity_payloads = encode_parity_pages(data_page_payloads, config.redundancy_pages)

    images: list[Image.Image] = []
    for r_idx, pp in enumerate(parity_payloads):
        page_idx = data_pages + r_idx
        syms = bytes_to_symbols(pp, config.num_colors)
        grid = _sparse_symbol_grid(syms, cols, rows, valid_order)
        image = render_page(
            grid, page_idx, total_pages, data_pages,
            sha256_hash, file_size, config, flags,
        )
        images.append(image)
        if on_page_complete:
            on_page_complete(page_idx, total_pages, None)
    return images
