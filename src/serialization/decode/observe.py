from typing import NamedTuple

import numpy as np

from common.geometry import page_geometry
from common.page_bytes import page_byte_plan, symbol_count_for_bytes
from common.page_layout import data_capacity_bytes, valid_cells_ordered
from serialization.decode.calibrate import calibration_offset_and_refs
from serialization.decode.classify import classify_cells
from serialization.decode.detect_tags import detect_tags
from serialization.decode.erasures import bytes_and_erasures
from serialization.decode.errors import DecodeError
from serialization.decode.header_config import config_from_header
from serialization.decode.read_qr import read_qr_header
from serialization.decode.warp_mesh import warp_page
from serialization.encode.qr_header import DecodedQrHeader


class PageObservation(NamedTuple):
    header: DecodedQrHeader
    data: bytes
    erasures: tuple[int, ...]
    symbols: tuple[int, ...]
    confidence: tuple[float, ...]


def observe_page(image: np.ndarray, model: object | None) -> PageObservation:
    rotated, header, qr_points = read_qr_header(image)
    config = config_from_header(header)
    geometry = page_geometry(config)
    if (geometry.cols, geometry.rows) != (header.cols, header.rows):
        raise DecodeError(
            f"header grid {header.cols}x{header.rows} does not match geometry {geometry.cols}x{geometry.rows}"
        )
    detected = detect_tags(rotated, {tag.tag_id for tag in geometry.tags})
    warped = warp_page(rotated, geometry, detected, qr_points)
    dx, dy, refs = calibration_offset_and_refs(warped, geometry, config)
    symbols, confidence = classify_cells(
        warped, geometry, config, dx, dy, refs, model, valid_cells_ordered(config),
    )
    plan = page_byte_plan(header.payload_length, data_capacity_bytes(config), header.data_pages, header.num_symbols)
    nbytes = plan.read_len[header.page_index] if header.page_index < header.data_pages else plan.parity_len
    needed = symbol_count_for_bytes(nbytes, header.num_symbols)
    chosen = list(symbols[:needed])
    conf = list(confidence[:needed])
    if len(chosen) < needed:
        chosen.extend([0] * (needed - len(chosen)))
        conf.extend([0.0] * (needed - len(conf)))
    data, erasures = bytes_and_erasures(chosen, conf, header.num_symbols, nbytes)
    return PageObservation(header, data, tuple(erasures), tuple(chosen), tuple(conf))
