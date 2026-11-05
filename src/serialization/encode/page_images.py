import logging
from collections.abc import Iterator
from pathlib import Path

from PIL import Image

from common.config import PaperClipConfig
from serialization.encode.encoder import compute_total_pages, payload_to_symbol_grids, prepare_payload
from serialization.encode.fit_ecc import fill_config
from serialization.encode.frame_payload import PreparedPayload
from serialization.encode.parity_render import render_parity_pages
from serialization.encode.renderer import render_page

logger = logging.getLogger(__name__)


def document_plan(
    input_path: Path,
    config: PaperClipConfig,
    passphrase: str | None,
    prepared: PreparedPayload | None,
) -> tuple[PaperClipConfig, PreparedPayload, int, int]:
    if prepared is None:
        raw_data = input_path.read_bytes()
        logger.info("Read %d bytes from %s", len(raw_data), input_path)
        config = fill_config(raw_data, config, input_path.name)
        prepared = prepare_payload(raw_data, config, filename=input_path.name, passphrase=passphrase)
    data_pages = compute_total_pages(len(prepared.payload), config)
    total_pages = data_pages + config.redundancy_pages
    return config, prepared, data_pages, total_pages


def each_page(
    config: PaperClipConfig,
    prepared: PreparedPayload,
    data_pages: int,
    total_pages: int,
    duplex: bool = False,
) -> Iterator[tuple[int, Image.Image]]:
    grids = payload_to_symbol_grids(prepared.payload, config, data_pages)
    for page_idx, grid in enumerate(grids):
        yield page_idx, render_page(grid, page_idx, total_pages, data_pages, prepared, config, duplex)
    if config.redundancy_pages <= 0:
        return
    parity = render_parity_pages(prepared.payload, config, data_pages, total_pages, prepared, None, duplex)
    for offset, image in enumerate(parity):
        yield data_pages + offset, image
