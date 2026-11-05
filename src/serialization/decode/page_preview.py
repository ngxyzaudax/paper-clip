import cv2
import numpy as np

PREVIEW_LONG_SIDE = 2400


def page_preview(warped: np.ndarray) -> tuple[np.ndarray, float]:
    """The rectified scan shrunk for damage maps, with the factor from page pixels to preview pixels."""
    height, width = warped.shape[:2]
    scale = min(1.0, PREVIEW_LONG_SIDE / max(height, width))
    if scale >= 1.0:
        return warped.copy(), 1.0
    size = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    return cv2.resize(warped, size, interpolation=cv2.INTER_AREA), scale
