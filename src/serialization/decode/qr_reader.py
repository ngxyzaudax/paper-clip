import logging

import numpy as np
from pyzbar.pyzbar import ZBarSymbol
from pyzbar.pyzbar import decode as pyzbar_decode

from common.config import HEADER_STRUCT, MAGIC, PaperClipConfig
from common.page_layout import margin_offset, metadata_band_height, usable_area_px
from common.types import HeaderData, RGB
from serialization.encode.palette_qr import decode_palette_bytes, qr_payload_to_palette
from serialization.encode.qr_header import decode_header_bytes, qr_payload_to_header

logger = logging.getLogger(__name__)


def _crop_qr_search_area(image: np.ndarray, config: PaperClipConfig) -> np.ndarray:
    mx, my = margin_offset(config)
    usable_w, _ = usable_area_px(config)
    band_h = metadata_band_height(config)
    search_w = min(usable_w, image.shape[1] - mx)
    search_h = min(band_h + 50, image.shape[0] - my)
    return image[my : my + search_h, mx : mx + search_w]


def read_qr_header(image: np.ndarray, config: PaperClipConfig | None = None) -> HeaderData | None:
    if config is not None:
        crop = _crop_qr_search_area(image, config)
        header = _try_decode_qr(crop)
        if header is not None:
            return header

    header = _try_decode_qr(image)
    return header


def _try_decode_qr(image: np.ndarray) -> HeaderData | None:
    results = pyzbar_decode(image, symbols=[ZBarSymbol.QRCODE])
    for result in results:
        try:
            raw = qr_payload_to_header(result.data)
        except Exception:
            continue
        if len(raw) < HEADER_STRUCT.size:
            continue
        if raw[:4] != MAGIC:
            continue
        try:
            header = decode_header_bytes(raw)
            logger.info(
                "QR header decoded: v%d colors=%d cell=%d page=%d/%d",
                header.version, header.num_colors, header.cell_size_px,
                header.page_index, header.total_pages,
            )
            return header
        except Exception:
            logger.warning("QR data matched magic but failed struct unpack")
    return None


def read_palette_qr(
    image: np.ndarray, config: PaperClipConfig,
) -> tuple[RGB, ...] | None:
    crop = _crop_qr_search_area(image, config)
    results = pyzbar_decode(crop, symbols=[ZBarSymbol.QRCODE])
    for result in results:
        if not result.data:
            continue
        raw = qr_payload_to_palette(result.data)
        if raw is None:
            continue
        palette = decode_palette_bytes(raw)
        if palette is not None:
            logger.info("Palette QR decoded: %d colors", len(palette))
            return palette
    return None
