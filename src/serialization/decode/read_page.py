import numpy as np

from common.config import PaperClipConfig
from common.geometry import page_geometry
from common.page_bytes import page_byte_plan, symbol_count_for_bytes
from common.page_layout import data_capacity_bytes, valid_cells_ordered
from serialization.decode.calibrate import calibration_offset_and_refs
from serialization.decode.classify import classify_cells
from serialization.decode.detect_tags import detect_tags
from serialization.decode.erasures import bytes_and_erasures
from serialization.decode.errors import DecodeError
from serialization.decode.header_config import config_from_header
from serialization.decode.observation import PageObservation
from serialization.decode.page_preview import page_preview
from serialization.decode.qr_copies import readable_slots
from serialization.decode.qr_multi import QrHit
from serialization.decode.restore import restore_page
from serialization.decode.warp_mesh import warp_page
from serialization.encode.header_bytes import DecodedQrHeader


def read_page(
    image: np.ndarray,
    header: DecodedQrHeader,
    hits: tuple[QrHit, ...],
    model: object | None,
    source: str,
    inferred_from: int,
) -> PageObservation:
    config = config_from_header(header)
    geometry = page_geometry(config)
    if (geometry.cols, geometry.rows) != (header.cols, header.rows):
        raise DecodeError(
            f"header grid {header.cols}x{header.rows} does not match geometry {geometry.cols}x{geometry.rows}"
        )
    detected = detect_tags(image, {tag.tag_id for tag in geometry.tags})
    quads = tuple(hit.points for hit in hits if len(hit.points) == 4)
    primary = quads[0] if quads else None
    warped = warp_page(image, geometry, detected, primary, tuple(quads[1:]))
    return page_from_warped(warped, config, header, model, source, inferred_from)


def page_from_warped(
    warped: np.ndarray,
    config: PaperClipConfig,
    header: DecodedQrHeader,
    model: object | None,
    source: str,
    inferred_from: int,
) -> PageObservation:
    geometry = page_geometry(config)
    colour = restore_page(warped)
    dx, dy, refs = calibration_offset_and_refs(colour, geometry, config)
    nbytes = _nbytes(header, config)
    symbols, confidence = classify_cells(
        warped, geometry, config, dx, dy, refs, model, valid_cells_ordered(config), colour,
    )
    chosen, conf = _fit(symbols, confidence, symbol_count_for_bytes(nbytes, header.num_symbols))
    data, erasures = bytes_and_erasures(chosen, conf, header.num_symbols, nbytes)
    slots = readable_slots(warped, geometry)
    preview, scale = page_preview(warped)
    return PageObservation(
        header, data, tuple(erasures), tuple(chosen), tuple(conf), preview, scale, (dx, dy),
        source, sum(slots), slots, inferred_from,
    )


def _nbytes(header: DecodedQrHeader, config: PaperClipConfig) -> int:
    capacity = data_capacity_bytes(config)
    if header.page_index < 0:
        return capacity
    plan = page_byte_plan(header.payload_length, capacity, header.data_pages, header.num_symbols)
    if header.page_index < header.data_pages:
        return plan.read_len[header.page_index]
    return plan.parity_len


def _fit(symbols: list[int], confidence: list[float], needed: int) -> tuple[list[int], list[float]]:
    chosen = list(symbols[:needed])
    conf = list(confidence[:needed])
    if len(chosen) < needed:
        chosen.extend([0] * (needed - len(chosen)))
        conf.extend([0.0] * (needed - len(conf)))
    return chosen, conf
