import logging

import numpy as np

from common.config import MAGIC, PaperClipConfig
from common.page_layout import page_image_size
from common.types import HeaderData
from serialization.decode.deskew import apply_deskew, compute_transform
from serialization.decode.finder_detect import detect_markers_with_corners
from serialization.decode.qr_reader import read_qr_header

logger = logging.getLogger(__name__)


def detect_markers(
    image: np.ndarray,
) -> tuple[list[tuple[float, float]], dict[int, np.ndarray] | None]:
    markers, tag_corners = detect_markers_with_corners(image)
    if len(markers) < 4:
        logger.warning("Found only %d finder markers", len(markers))
    return markers, tag_corners


def config_from_header(header: HeaderData) -> PaperClipConfig:
    from common.config import BLOCK_SIZE
    ecc = header.ecc_symbols
    redundancy = ecc / BLOCK_SIZE if ecc > 0 else 0.20
    return PaperClipConfig(
        num_colors=header.num_colors,
        cell_size_px=header.cell_size_px,
        scan_dpi=header.scan_dpi if header.scan_dpi > 0 else 1200,
        rs_redundancy=redundancy,
    )


def _needs_deskew(image: np.ndarray, config: PaperClipConfig) -> bool:
    expected_w, expected_h = page_image_size(config)
    h, w = image.shape[:2]
    return not (w == expected_w and h == expected_h)


def _deskew_with_config(
    image: np.ndarray,
    markers: list[tuple[float, float]],
    config: PaperClipConfig,
    tag_corners: dict[int, np.ndarray] | None = None,
) -> np.ndarray:
    if not _needs_deskew(image, config):
        return image
    if len(markers) < 4:
        return image
    transform = compute_transform(markers, config, tag_corners)
    return apply_deskew(image, transform, config)


def _empty_header() -> HeaderData:
    return HeaderData(
        magic=b"", version=0, flags=0, num_colors=0, cell_size_px=0,
        ecc_symbols=0, scan_dpi=0, grid_cols=0, grid_rows=0,
        page_index=0, total_pages=0, data_pages=0, data_length=0,
        sha256_hash=b"", header_crc=0, crc_valid=False,
    )


def align_and_read_header(
    image: np.ndarray,
    markers: list[tuple[float, float]],
    default_config: PaperClipConfig,
    tag_corners: dict[int, np.ndarray] | None = None,
) -> tuple[np.ndarray, HeaderData]:
    deskewed = _deskew_with_config(image, markers, default_config, tag_corners)
    header = read_qr_header(deskewed, default_config)
    if header is not None and header.magic == MAGIC and header.crc_valid:
        actual = config_from_header(header)
        config_differs = (
            actual.cell_size_px != default_config.cell_size_px
            or actual.scan_dpi != default_config.scan_dpi
        )
        if config_differs and len(markers) >= 4:
            deskewed = _deskew_with_config(image, markers, actual, tag_corners)
        return deskewed, header

    header = read_qr_header(image)
    if header is not None and header.magic == MAGIC and header.crc_valid:
        actual = config_from_header(header)
        if len(markers) >= 4:
            deskewed = _deskew_with_config(image, markers, actual, tag_corners)
        return deskewed, header

    return deskewed, _empty_header()
