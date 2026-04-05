import logging
from pathlib import Path

from PIL import Image

from common.config import FLAG_ENCRYPTED, PaperClipConfig
from serialization.encode.encoder import (
    compute_total_pages,
    payload_to_symbol_grids,
    prepare_payload,
)
from serialization.encode.parity_render import OnPageComplete, render_parity_pages
from serialization.encode.renderer import render_page

logger = logging.getLogger(__name__)


def render_pages(
    input_path: Path,
    config: PaperClipConfig,
    on_page_complete: OnPageComplete | None = None,
    flags: int = 0,
    passphrase: str | None = None,
) -> list[Image.Image]:
    if passphrase:
        flags |= FLAG_ENCRYPTED
    raw_data = input_path.read_bytes()
    file_size = len(raw_data)
    logger.info("Read %d bytes from %s", file_size, input_path)
    payload, sha256_hash = prepare_payload(
        raw_data, config, filename=input_path.name, passphrase=passphrase,
    )
    data_pages = compute_total_pages(len(payload), config)
    total_pages = data_pages + config.redundancy_pages
    logger.info("Rendering %d data + %d parity = %d page(s)",
                data_pages, config.redundancy_pages, total_pages)
    grids = payload_to_symbol_grids(payload, config, data_pages)

    images: list[Image.Image] = []
    for page_idx, grid in enumerate(grids):
        image = render_page(
            grid, page_idx, total_pages, data_pages,
            sha256_hash, file_size, config, flags,
        )
        images.append(image)
        if on_page_complete:
            on_page_complete(page_idx, total_pages, None)

    if config.redundancy_pages > 0:
        images.extend(render_parity_pages(
            payload, config, data_pages, total_pages,
            sha256_hash, file_size, flags, on_page_complete,
        ))
    return images


def _output_paths(base: Path, n: int) -> list[Path]:
    if n == 1:
        return [base.with_suffix(".png")]
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
        img.save(str(path), format="PNG", compress_level=1, dpi=(config.print_dpi, config.print_dpi))
        logger.info("Saved %s (%dx%d, lossless PNG @ %d dpi)", path, img.width, img.height, config.print_dpi)
    return paths
