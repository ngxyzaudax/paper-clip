import cv2
import numpy as np

from common.geometry import PageGeometry
from common.types import Region
from serialization.decode.qr_binary import binary_views
from serialization.decode.qr_detect import detect, detectors, header_from_text, views


def readable_slots(warped: np.ndarray, geometry: PageGeometry) -> tuple[bool, ...]:
    return tuple(_reads(warped, geometry, slot.qr) for slot in geometry.slots)


def _reads(warped: np.ndarray, geometry: PageGeometry, region: Region) -> bool:
    crop = _crop(warped, geometry, region)
    if crop.size == 0:
        return False
    found = detectors()
    for view in (*views(crop), *binary_views(crop)):
        for detector in found:
            text, _points = detect(detector, view)
            if header_from_text(text) is not None:
                return True
    return False


def _crop(warped: np.ndarray, geometry: PageGeometry, region: Region) -> np.ndarray:
    height, width = warped.shape[:2]
    x0 = max(0, geometry.origin_x + region.x)
    y0 = max(0, geometry.origin_y + region.y)
    x1 = min(width, x0 + region.width)
    y1 = min(height, y0 + region.height)
    crop = warped[y0:y1, x0:x1]
    if crop.size == 0:
        return crop
    border = max(8, geometry.cell // 2)
    return cv2.copyMakeBorder(
        crop, border, border, border, border, cv2.BORDER_CONSTANT, value=(255, 255, 255),
    )
