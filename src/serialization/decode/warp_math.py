import cv2
import numpy as np

from common.format_spec import QR_BORDER_MODULES, qr_module_count
from common.geometry import PageGeometry


def homography(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    if len(src) == 4:
        return cv2.getPerspectiveTransform(src.astype(np.float32), dst.astype(np.float32))
    found, _mask = cv2.findHomography(src.astype(np.float32), dst.astype(np.float32), cv2.RANSAC, 4.0)
    if found is None:
        return cv2.getPerspectiveTransform(src[:4].astype(np.float32), dst[:4].astype(np.float32))
    return found


def project(matrix: np.ndarray, point: np.ndarray) -> np.ndarray:
    vec = matrix @ np.array([float(point[0]), float(point[1]), 1.0], np.float64)
    if abs(float(vec[2])) < 1e-8:
        return point.astype(np.float32)
    return np.array([vec[0] / vec[2], vec[1] / vec[2]], np.float32)


def warp_global(image: np.ndarray, matrix: np.ndarray, width: int, height: int) -> np.ndarray:
    return cv2.warpPerspective(
        image, matrix, (width, height),
        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255),
    )


def qr_code_corners(geometry: PageGeometry) -> np.ndarray:
    modules = qr_module_count()
    border = geometry.qr.width * QR_BORDER_MODULES / modules
    x = float(geometry.origin_x + geometry.qr.x) + border
    y = float(geometry.origin_y + geometry.qr.y) + border
    side = float(geometry.qr.width) - 2.0 * border
    return np.array([[x, y], [x + side, y], [x + side, y + side], [x, y + side]], np.float32)


def order_quad(points: np.ndarray) -> np.ndarray:
    pts = np.asarray(points, np.float32).reshape(-1, 2)
    sums = pts.sum(axis=1)
    diff = pts[:, 0] - pts[:, 1]
    return np.stack([
        pts[np.argmin(sums)],
        pts[np.argmax(diff)],
        pts[np.argmax(sums)],
        pts[np.argmin(diff)],
    ])


def vstack(base: np.ndarray, extra: np.ndarray) -> np.ndarray:
    if len(base) == 0:
        return extra.astype(np.float32)
    return np.vstack([base, extra]).astype(np.float32)


def quad_area(points: np.ndarray) -> float:
    x, y = points[:, 0], points[:, 1]
    return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) * 0.5)
