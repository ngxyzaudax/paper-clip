import logging

import numpy as np

from serialization.decode.errors import DecodeError
from serialization.decode.grid_page import try_grid_page
from serialization.decode.header_candidates import candidate_configs
from serialization.decode.observation import PageObservation
from serialization.decode.read_page import read_page
from serialization.decode.read_qr import locate_qr_headers
from serialization.encode.header_bytes import DecodedQrHeader

logger = logging.getLogger(__name__)


def observe_page(
    image: np.ndarray,
    model: object | None,
    hints: tuple[DecodedQrHeader, ...] = (),
) -> PageObservation:
    located = locate_qr_headers(image)
    if located is not None:
        rotated, hits = located
        return _logged(read_page(rotated, hits[0].header, hits, model, "qr", -1))
    for config in candidate_configs(hints):
        page = try_grid_page(image, config, model)
        if page is not None:
            return _logged(page)
    orphan = _orphan(image, hints, model)
    if orphan is not None:
        return _logged(orphan)
    raise DecodeError("page header not found")


def _orphan(
    image: np.ndarray,
    hints: tuple[DecodedQrHeader, ...],
    model: object | None,
) -> PageObservation | None:
    if not hints:
        return None
    header = hints[0]
    try:
        return read_page(image, header._replace(page_index=-1), (), model, "orphan", header.page_index)
    except DecodeError:
        return None


def _logged(page: PageObservation) -> PageObservation:
    logger.info(
        "Page header via %s (%d/%d QR copies)",
        page.header_source,
        page.qr_copies_read,
        len(page.qr_slots_read),
    )
    return page
