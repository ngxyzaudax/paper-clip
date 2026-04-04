from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from common.config import FLAG_ENCRYPTED, PaperClipConfig
from common.types import PageInfo
from serialization.encode.renderer import render_page

OnPageComplete = Callable[[int, int, Path | None], None]


def make_page_info(
    input_path: Path, file_size: int, page_idx: int,
    total_pages: int, data_pages: int, sha256_hash: bytes, flags: int,
) -> PageInfo:
    return PageInfo(
        filename=input_path.name,
        file_size=file_size,
        page_index=page_idx,
        total_pages=total_pages,
        data_pages=data_pages,
        sha256_hash=sha256_hash,
        encrypted=bool(flags & FLAG_ENCRYPTED),
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


def extract_page_payloads(
    payload: bytes, config: PaperClipConfig, data_pages: int,
) -> list[bytes]:
    from common.page_layout import grid_dimensions
    from common.symbols import bytes_to_symbols, chunk_params, symbol_count
    from common.symbols import symbols_to_bytes as syms_to_raw

    symbols = bytes_to_symbols(payload, config.num_colors)
    cols, rows = grid_dimensions(config)
    cells_per_page = cols * rows
    k, m = chunk_params(symbol_count(config.num_colors))
    page_payloads: list[bytes] = []
    for page in range(data_pages):
        start = page * cells_per_page
        ps = symbols[start : start + cells_per_page]
        ps = ps + [0] * (cells_per_page - len(ps))
        page_payloads.append(syms_to_raw(ps, config.num_colors, (len(ps) // m) * k))
    return page_payloads


def render_parity_pages(
    payload: bytes, config: PaperClipConfig, data_pages: int, total_pages: int,
    sha256_hash: bytes, file_size: int, flags: int,
    input_path: Path, on_page_complete: OnPageComplete | None,
) -> list[Image.Image]:
    from common.fountain import encode_parity_pages
    from common.page_layout import grid_dimensions
    from common.symbols import bytes_to_symbols

    cols, rows = grid_dimensions(config)
    cells_per_page = cols * rows
    data_page_payloads = extract_page_payloads(payload, config, data_pages)
    parity_payloads = encode_parity_pages(data_page_payloads, config.redundancy_pages)

    images: list[Image.Image] = []
    for r_idx, pp in enumerate(parity_payloads):
        page_idx = data_pages + r_idx
        syms = bytes_to_symbols(pp, config.num_colors)
        syms = syms + [0] * max(0, cells_per_page - len(syms))
        grid = [syms[row * cols : (row + 1) * cols] for row in range(rows)]
        info = make_page_info(
            input_path, file_size, page_idx, total_pages, data_pages, sha256_hash, flags,
        )
        image = render_page(
            grid, page_idx, total_pages, data_pages,
            sha256_hash, file_size, config, flags, info,
        )
        images.append(image)
        if on_page_complete:
            on_page_complete(page_idx, total_pages, None)
    return images
