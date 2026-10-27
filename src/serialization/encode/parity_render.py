from collections.abc import Callable
from pathlib import Path

from PIL import Image

from common.config import PaperClipConfig
from common.fountain import encode_parity_pages
from common.page_bytes import page_byte_plan
from common.page_layout import data_capacity_bytes, grid_dimensions, valid_cells_ordered
from common.symbols import bytes_to_symbols
from serialization.encode.encoder import _sparse_symbol_grid
from serialization.encode.frame_payload import PreparedPayload
from serialization.encode.renderer import render_page

OnPageComplete = Callable[[int, int, Path | None], None]


def render_parity_pages(
    payload: bytes,
    config: PaperClipConfig,
    data_pages: int,
    total_pages: int,
    prepared: PreparedPayload,
    on_page_complete: OnPageComplete | None,
) -> list[Image.Image]:
    cols, rows = grid_dimensions(config)
    valid_order = valid_cells_ordered(config)
    plan = page_byte_plan(len(payload), data_capacity_bytes(config), data_pages, config.num_symbols)
    chunks = [
        payload[index * data_capacity_bytes(config):][:plan.slice_len[index]].ljust(plan.read_len[index], b"\x00")
        for index in range(data_pages)
    ]
    images: list[Image.Image] = []
    for offset, parity in enumerate(encode_parity_pages(chunks, config.redundancy_pages)):
        page_idx = data_pages + offset
        grid = _sparse_symbol_grid(bytes_to_symbols(parity, config.num_symbols), cols, rows, valid_order)
        image = render_page(grid, page_idx, total_pages, data_pages, prepared, config)
        images.append(image)
        if on_page_complete:
            on_page_complete(page_idx, total_pages, None)
    return images
