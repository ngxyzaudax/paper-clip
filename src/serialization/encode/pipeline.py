import logging
from pathlib import Path

from PIL import Image

from common.config import PaperClipConfig
from common.perf import log_phase
from serialization.encode.encoder import compute_total_pages, payload_to_symbol_grids, prepare_payload
from serialization.encode.frame_payload import PreparedPayload
from serialization.encode.parity_render import OnPageComplete, render_parity_pages
from serialization.encode.renderer import render_page

logger = logging.getLogger(__name__)


def render_pages(
    input_path: Path,
    config: PaperClipConfig,
    on_page_complete: OnPageComplete | None = None,
    passphrase: str | None = None,
    prepared: PreparedPayload | None = None,
) -> list[Image.Image]:
    if prepared is None:
        with log_phase(logger, "render_pages.read_input"):
            raw_data = input_path.read_bytes()
        logger.info("Read %d bytes from %s", len(raw_data), input_path)
        with log_phase(logger, "render_pages.prepare_payload"):
            prepared = prepare_payload(raw_data, config, filename=input_path.name, passphrase=passphrase)
    data_pages = compute_total_pages(len(prepared.payload), config)
    total_pages = data_pages + config.redundancy_pages
    logger.info(
        "Rendering %d data + %d parity = %d page(s)",
        data_pages, config.redundancy_pages, total_pages,
    )
    with log_phase(logger, "render_pages.payload_to_symbol_grids"):
        grids = payload_to_symbol_grids(prepared.payload, config, data_pages)
    images: list[Image.Image] = []
    with log_phase(logger, "render_pages.render_data_pages"):
        for page_idx, grid in enumerate(grids):
            image = render_page(grid, page_idx, total_pages, data_pages, prepared, config)
            images.append(image)
            if on_page_complete:
                on_page_complete(page_idx, total_pages, None)
    if config.redundancy_pages > 0:
        with log_phase(logger, "render_pages.render_parity_pages"):
            images.extend(render_parity_pages(
                prepared.payload, config, data_pages, total_pages, prepared, on_page_complete,
            ))
    return images


def _output_paths(base: Path, count: int) -> list[Path]:
    if count == 1:
        return [base.with_suffix(".png")]
    return [base.parent / f"{base.stem}_{index + 1:03d}.png" for index in range(count)]


def encode(
    input_path: Path,
    output_base: Path,
    config: PaperClipConfig,
    on_page_complete: OnPageComplete | None = None,
    passphrase: str | None = None,
    prepared: PreparedPayload | None = None,
) -> list[Path]:
    images = render_pages(input_path, config, on_page_complete, passphrase, prepared=prepared)
    output_base.parent.mkdir(parents=True, exist_ok=True)
    paths = _output_paths(output_base, len(images))
    with log_phase(logger, "encode.write_png_files"):
        for img, path in zip(images, paths):
            img.save(str(path), format="PNG", compress_level=1, dpi=(config.print_dpi, config.print_dpi))
            logger.info("Saved %s (%dx%d, lossless PNG @ %d dpi)", path, img.width, img.height, config.print_dpi)
    return paths
