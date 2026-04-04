import logging
from pathlib import Path

import numpy as np

from common.config import FORMAT_VERSION, MAGIC, PaperClipConfig
from common.image_resolver import load_image, resolve_input_images
from common.types import HeaderData
from serialization.decode.align import align_and_read_header, detect_markers
from serialization.decode.multi_scan import average_scans

logger = logging.getLogger(__name__)


def load_pages(source: Path | list[np.ndarray]) -> list[tuple[np.ndarray, str]]:
    if isinstance(source, list):
        return [(img, f"page_{i}") for i, img in enumerate(source)]
    resolved = resolve_input_images(source)
    return [(load_image(p), str(p)) for p in resolved]


def process_raw_pages(
    pages: list[tuple[np.ndarray, str]],
) -> list[tuple[int, np.ndarray, HeaderData]]:
    temp_config = PaperClipConfig()
    raw_pages: list[tuple[int, np.ndarray, HeaderData]] = []
    for i, (image, label) in enumerate(pages):
        logger.info("Processing: %s", label)
        markers, tag_corners = detect_markers(image)
        deskewed, header = align_and_read_header(image, markers, temp_config, tag_corners)
        if header.magic != MAGIC:
            raise ValueError(f"Invalid magic bytes in {label}")
        if header.version != FORMAT_VERSION:
            raise ValueError(
                f"Unsupported format version {header.version} in {label} "
                f"(expected {FORMAT_VERSION})"
            )
        if not header.crc_valid:
            logger.warning("Header CRC mismatch in %s, attempting recovery", label)
        raw_pages.append((header.page_index, deskewed, header))
    return raw_pages


def load_and_sort_pages(
    source: Path | list[Path] | list[np.ndarray],
) -> list[tuple[int, np.ndarray, HeaderData]]:
    if isinstance(source, Path):
        pages = load_pages(source)
    elif isinstance(source, list) and source and isinstance(source[0], Path):
        pages = [(load_image(p), str(p)) for p in source]
    else:
        pages = [(img, f"page_{i}") for i, img in enumerate(source)]

    raw_pages = process_raw_pages(pages)
    sorted_pages = average_scans(raw_pages)
    if not sorted_pages:
        raise ValueError("No valid pages found in input. Cannot decode.")
    return sorted_pages
