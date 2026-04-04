import logging
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from common.config import FLAG_ENCRYPTED, FLAG_HAS_PALETTE_QR, PaperClipConfig
from common.types import PageInfo
from serialization.encode.encoder import (
    compute_total_pages,
    payload_to_symbol_grids,
    prepare_payload,
)
from serialization.encode.renderer import render_page

logger = logging.getLogger(__name__)

OnPageComplete = Callable[[int, int, Path | None], None]


def _make_page_info(
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


def render_pages(
    input_path: Path,
    config: PaperClipConfig,
    on_page_complete: OnPageComplete | None = None,
    flags: int = 0,
    passphrase: str | None = None,
) -> list[Image.Image]:
    if passphrase:
        flags |= FLAG_ENCRYPTED
    if config.calibrated_colors:
        flags |= FLAG_HAS_PALETTE_QR
    raw_data = input_path.read_bytes()
    file_size = len(raw_data)
    logger.info("Read %d bytes from %s", file_size, input_path)
    data_pages = compute_total_pages(file_size, config)
    total_pages = data_pages + config.redundancy_pages
    logger.info("Rendering %d data + %d parity = %d page(s)",
                data_pages, config.redundancy_pages, total_pages)
    payload, sha256_hash = prepare_payload(
        raw_data, config, filename=input_path.name, passphrase=passphrase,
    )
    grids = payload_to_symbol_grids(payload, config, data_pages)

    images: list[Image.Image] = []
    for page_idx, grid in enumerate(grids):
        info = _make_page_info(
            input_path, file_size, page_idx, total_pages, data_pages, sha256_hash, flags,
        )
        image = render_page(
            grid, page_idx, total_pages, data_pages,
            sha256_hash, file_size, config, flags, info,
        )
        images.append(image)
        if on_page_complete:
            on_page_complete(page_idx, total_pages, None)

    if config.redundancy_pages > 0:
        images.extend(_render_parity_pages(
            payload, config, data_pages, total_pages,
            sha256_hash, file_size, flags, input_path, on_page_complete,
        ))
    return images


def _render_parity_pages(
    payload: bytes, config: PaperClipConfig, data_pages: int, total_pages: int,
    sha256_hash: bytes, file_size: int, flags: int,
    input_path: Path, on_page_complete: OnPageComplete | None,
) -> list[Image.Image]:
    from common.fountain import encode_parity_pages
    from common.symbols import bytes_to_symbols
    from common.page_layout import grid_dimensions

    cols, rows = grid_dimensions(config)
    cells_per_page = cols * rows
    data_page_payloads = _extract_page_payloads(payload, config, data_pages)
    parity_payloads = encode_parity_pages(data_page_payloads, config.redundancy_pages)

    images = []
    for r_idx, pp in enumerate(parity_payloads):
        page_idx = data_pages + r_idx
        syms = bytes_to_symbols(pp, config.num_colors)
        syms = syms + [0] * max(0, cells_per_page - len(syms))
        grid = [syms[row * cols : (row + 1) * cols] for row in range(rows)]
        info = _make_page_info(
            input_path, file_size, page_idx, total_pages, data_pages, sha256_hash, flags,
        )
        image = render_page(
            grid, page_idx, total_pages, data_pages,
            sha256_hash, file_size, config, flags, info,
        )
        images.append(image)
        if on_page_complete: on_page_complete(page_idx, total_pages, None)
    return images


def _extract_page_payloads(
    payload: bytes, config: PaperClipConfig, data_pages: int,
) -> list[bytes]:
    from common.symbols import bytes_to_symbols, chunk_params, symbol_count, symbols_to_bytes as syms_to_raw
    from common.page_layout import grid_dimensions
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


def _output_paths(base: Path, n: int) -> list[Path]:
    if n == 1: return [base.with_suffix(".png")]
    return [base.parent / f"{base.stem}_{i + 1:03d}.png" for i in range(n)]


def encode(
    input_path: Path,
    output_base: Path,
    config: PaperClipConfig,
    on_page_complete: OnPageComplete | None = None,
    flags: int = 0,
    passphrase: str | None = None,
) -> list[Path]:
    images = render_pages(input_path, config, on_page_complete, flags, passphrase)
    output_base.parent.mkdir(parents=True, exist_ok=True)
    paths = _output_paths(output_base, len(images))
    for img, path in zip(images, paths):
        img.save(str(path), format="PNG", compress_level=1, dpi=(config.scan_dpi, config.scan_dpi))
        logger.info("Saved %s (%dx%d, lossless PNG @ %d dpi)", path, img.width, img.height, config.scan_dpi)
    return paths
