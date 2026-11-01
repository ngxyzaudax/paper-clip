import math

import cv2
import numpy as np


def page_rotation(matrix: np.ndarray) -> int:
    """Quarter-turn rotation of the sheet in the scan, in degrees, derived from the frame homography."""
    points = np.array([[[105.0, 148.0], [155.0, 148.0]]], np.float64)
    mapped = cv2.perspectiveTransform(points, matrix).reshape(2, 2)
    dx, dy = mapped[1] - mapped[0]
    angle = math.degrees(math.atan2(dy, dx)) % 360.0
    return int(round(angle / 90.0)) % 4 * 90
