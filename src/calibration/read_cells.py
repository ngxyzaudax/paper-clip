import numpy as np

from common.config import PaperClipConfig
from common.geometry_types import PageGeometry
from common.page_layout import valid_cells_ordered
from serialization.decode.calibrate import calibration_offset_and_refs
from serialization.decode.classify import classify_cells
from serialization.decode.restore import restore_page
from serialization.decode.warp_mesh import warp_page


def classified_symbols(
    image: np.ndarray,
    geometry: PageGeometry,
    config: PaperClipConfig,
    detected: dict[int, np.ndarray],
    qr_points: np.ndarray | None,
    model: object | None,
    extra_points: tuple[np.ndarray, ...] = (),
) -> list[int]:
    warped = warp_page(image, geometry, detected, qr_points, extra_points)
    colour = restore_page(warped)
    dx, dy, refs = calibration_offset_and_refs(colour, geometry, config)
    symbols, _confidence = classify_cells(
        warped, geometry, config, dx, dy, refs, model, valid_cells_ordered(config), colour,
    )
    return symbols
