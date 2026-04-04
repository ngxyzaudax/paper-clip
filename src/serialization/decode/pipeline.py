import logging
from collections.abc import Callable
from pathlib import Path
from typing import Literal

import numpy as np

from common.config import FLAG_ENCRYPTED, FLAG_HAS_PALETTE_QR, PaperClipConfig
from common.types import HeaderData
from serialization.decode.align import config_from_header
from serialization.decode.calibrator import extract_calibration_references
from serialization.decode.decoder import grid_to_raw_bytes, raw_payload_to_bytes, symbols_to_bytes
from serialization.decode.grid_align import find_grid_offset
from serialization.decode.grid_reader import (
    classify_cells_ml,
    classify_cells_vectorized,
    locate_data_grid,
    sample_cells_vectorized,
)
from serialization.decode.page_loader import load_and_sort_pages

logger = logging.getLogger(__name__)

OnPageDecoded = Callable[[int, int, Path | None], None]
ClassifierMode = Literal["auto", "ml", "rgb"]


def _try_read_palette(
    deskewed_image: np.ndarray, config: PaperClipConfig,
) -> PaperClipConfig:
    from dataclasses import replace
    from serialization.decode.qr_reader import read_palette_qr
    palette = read_palette_qr(deskewed_image, config)
    if palette:
        return replace(config, calibrated_colors=palette)
    logger.debug("Palette QR flag set but palette not recovered")
    return config


def _try_load_ml_model(
    config: PaperClipConfig, mode: ClassifierMode = "auto",
) -> "object | None":
    if mode == "rgb":
        return None
    try:
        from common.config_store import detect_profile_name
        from ml.model import load_cell_classifier
        profile = detect_profile_name(config)
        if profile:
            model = load_cell_classifier(profile)
            if model:
                logger.info("Loaded ML classifier for profile: %s", profile)
                return model
        if mode == "ml":
            logger.warning("ML model requested but not found for config")
    except Exception as exc:
        logger.debug("ML model not available: %s", exc)
        if mode == "ml":
            logger.warning("ML model requested but failed to load: %s", exc)
    return None


def _decode_page(
    image: np.ndarray, config: PaperClipConfig, is_scan: bool = True,
    ml_model: "object | None" = None,
) -> list[list[int]]:
    references = extract_calibration_references(image, config)
    dx, dy = find_grid_offset(image, config, references, is_scan)
    grid_region = locate_data_grid(image, config, dx, dy)
    if ml_model is not None and is_scan:
        grid, _ = classify_cells_ml(grid_region, config, ml_model)
        return grid
    cell_averages = sample_cells_vectorized(grid_region, config)
    return classify_cells_vectorized(cell_averages, references)


def _decode_with_fountain(
    sorted_pages: list[tuple[int, np.ndarray, HeaderData]],
    config: PaperClipConfig, first_header: HeaderData,
    is_scan: bool, on_page_decoded: OnPageDecoded | None,
    encrypted: bool, passphrase: str | None,
    ml_model: "object | None" = None,
) -> tuple[bytes, str]:
    from common.fountain import reconstruct_missing
    page_raw: dict[int, bytes] = {}
    for idx, (page_idx, image, _) in enumerate(sorted_pages):
        page_raw[page_idx] = grid_to_raw_bytes(_decode_page(image, config, is_scan, ml_model), config)
        if on_page_decoded:
            on_page_decoded(idx, len(sorted_pages), None)
    dp = first_header.data_pages
    if all(i in page_raw for i in range(dp)):
        concatenated = b"".join(page_raw[i] for i in range(dp))
    else:
        recovered = reconstruct_missing(page_raw, dp, first_header.total_pages)
        concatenated = b"".join(recovered)
    return raw_payload_to_bytes(
        concatenated, config, first_header.data_length,
        first_header.sha256_hash, encrypted, passphrase,
    )


def decode(
    source: Path | list[Path] | list[np.ndarray],
    output_path: Path,
    on_page_decoded: OnPageDecoded | None = None,
    passphrase: str | None = None,
    classifier: ClassifierMode = "auto",
) -> tuple[bytes, str]:
    is_scan = not (isinstance(source, list) and source and isinstance(source[0], np.ndarray))
    sorted_pages = load_and_sort_pages(source)
    first_header = sorted_pages[0][2]
    config = config_from_header(first_header)
    if first_header.flags & FLAG_HAS_PALETTE_QR:
        config = _try_read_palette(sorted_pages[0][1], config)
    encrypted = bool(first_header.flags & FLAG_ENCRYPTED)
    has_fountain = first_header.data_pages < first_header.total_pages
    ml_model = _try_load_ml_model(config, classifier)

    if has_fountain:
        result, original_filename = _decode_with_fountain(
            sorted_pages, config, first_header, is_scan,
            on_page_decoded, encrypted, passphrase, ml_model,
        )
    else:
        all_grids: list[list[list[int]]] = []
        for idx, (_, image, _) in enumerate(sorted_pages):
            all_grids.append(_decode_page(image, config, is_scan, ml_model))
            if on_page_decoded:
                on_page_decoded(idx, len(sorted_pages), None)
        result, original_filename = symbols_to_bytes(
            all_grids, config, first_header.data_length,
            first_header.sha256_hash, encrypted, passphrase,
        )

    final_path = output_path.parent / original_filename if original_filename else output_path
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_bytes(result)
    logger.info("Decoded %d bytes to %s", len(result), final_path)
    return result, original_filename
