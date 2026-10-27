import cv2
import numpy as np

from serialization.decode.warp_math import project, quad_area

_NEIGHBOURS = 8
_MIN_SPREAD_PX2 = 64.0


def local_source(
    ideal: np.ndarray,
    observed: np.ndarray,
    point: np.ndarray,
    fallback: np.ndarray,
    limit_px: float,
) -> np.ndarray:
    guess = project(fallback, point)
    if len(ideal) < 4:
        return guess
    order = np.argsort(np.linalg.norm(ideal - point, axis=1))[:_NEIGHBOURS]
    near_ideal = ideal[order]
    near_observed = observed[order]
    if _spread(near_ideal) < _MIN_SPREAD_PX2:
        return guess
    matrix, _mask = cv2.findHomography(near_ideal.astype(np.float32), near_observed.astype(np.float32), 0)
    if matrix is None:
        return guess
    fitted = project(matrix, point)
    if not np.all(np.isfinite(fitted)) or float(np.linalg.norm(fitted - guess)) > limit_px:
        return guess
    return fitted


def _spread(points: np.ndarray) -> float:
    hull = cv2.convexHull(points.astype(np.float32)).reshape(-1, 2)
    if len(hull) < 3:
        return 0.0
    return quad_area(hull)
