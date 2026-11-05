import logging
from pathlib import Path

from PIL import Image

from common.config import PaperClipConfig
from common.perf import log_phase
from serialization.encode.frame_payload import PreparedPayload
from serialization.encode.page_images import document_plan, each_page
from serialization.encode.parity_render import OnPageComplete, OnPageImage

logger = logging.getLogger(__name__)


def render_pages(
    input_path: Path,
    config: PaperClipConfig,
    on_page_complete: OnPageComplete | None = None,
    passphrase: str | None = None,
    prepared: PreparedPayload | None = None,
    duplex: bool = False,
) -> list[Image.Image]:
    config, prepared, data_pages, total_pages = document_plan(input_path, config, passphrase, prepared)
    _log_plan(data_pages, config.redundancy_pages, total_pages)
    images: list[Image.Image] = []
    with log_phase(logger, "render_pages.render"):
        for page_idx, image in each_page(config, prepared, data_pages, total_pages, duplex):
            images.append(image)
            _notify_path(on_page_complete, page_idx, total_pages, None)
    return images


def encode(
    input_path: Path,
    output_base: Path,
    config: PaperClipConfig,
    on_page_complete: OnPageComplete | None = None,
    passphrase: str | None = None,
    prepared: PreparedPayload | None = None,
    on_page_image: OnPageImage | None = None,
    duplex: bool = False,
) -> list[Path]:
    config, prepared, data_pages, total_pages = document_plan(input_path, config, passphrase, prepared)
    _log_plan(data_pages, config.redundancy_pages, total_pages)
    output_base.parent.mkdir(parents=True, exist_ok=True)
    paths = _output_paths(output_base, total_pages)
    written: list[Path] = []
    with log_phase(logger, "encode.write_png_files"):
        for page_idx, image in each_page(config, prepared, data_pages, total_pages, duplex):
            path = paths[page_idx]
            _save_page(image, path, config.print_dpi)
            written.append(path)
            _notify_path(on_page_complete, page_idx, total_pages, path)
            if on_page_image:
                on_page_image(page_idx, total_pages, image)
    return written


def _output_paths(base: Path, count: int) -> list[Path]:
    if count == 1:
        return [base.with_suffix(".png")]
    return [base.parent / f"{base.stem}_{index + 1:03d}.png" for index in range(count)]


def _save_page(image: Image.Image, path: Path, dpi: int) -> None:
    image.save(str(path), format="PNG", compress_level=1, dpi=(dpi, dpi))
    logger.info("Saved %s (%dx%d, lossless PNG @ %d dpi)", path, image.width, image.height, dpi)


def _notify_path(callback: OnPageComplete | None, page_idx: int, total: int, path: Path | None) -> None:
    if callback:
        callback(page_idx, total, path)


def _log_plan(data_pages: int, parity_pages: int, total_pages: int) -> None:
    logger.info("Rendering %d data + %d parity = %d page(s)", data_pages, parity_pages, total_pages)
