import numpy as np

from common.config import PaperClipConfig
from common.geometry import page_geometry
from serialization.decode.calibrate import calibration_offset_and_refs
from serialization.decode.detect_tags import detect_tags
from serialization.decode.errors import DecodeError
from serialization.decode.grid_header_read import read_grid_header
from serialization.decode.header_config import config_from_header
from serialization.decode.observation import PageObservation
from serialization.decode.read_page import page_from_warped, read_page
from serialization.decode.restore import restore_page
from serialization.decode.warp_mesh import warp_page


def try_grid_page(image: np.ndarray, config: PaperClipConfig, model: object | None) -> PageObservation | None:
    try:
        geometry = page_geometry(config)
        detected = detect_tags(image, {tag.tag_id for tag in geometry.tags})
        if len(detected) < 4:
            return None
        warped = warp_page(image, geometry, detected, None)
    except (DecodeError, ValueError):
        return None
    colour = restore_page(warped)
    dx, dy, refs = calibration_offset_and_refs(colour, geometry, config)
    header = read_grid_header(warped, geometry, config, dx, dy, refs, model, colour)
    if header is None:
        return None
    true = config_from_header(header)
    try:
        if _same_layout(config, true):
            return page_from_warped(warped, true, header, model, "grid", -1)
        return read_page(image, header, (), model, "grid", -1)
    except DecodeError:
        return None


def _same_layout(left: PaperClipConfig, right: PaperClipConfig) -> bool:
    first, second = page_geometry(left), page_geometry(right)
    return (
        first.cols, first.rows, first.cell, first.origin_x, first.origin_y, first.slots,
    ) == (
        second.cols, second.rows, second.cell, second.origin_x, second.origin_y, second.slots,
    )
