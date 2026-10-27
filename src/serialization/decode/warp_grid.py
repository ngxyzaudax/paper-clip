import cv2
import numpy as np

from common.geometry import PageGeometry, tag_center_xy
from serialization.decode.warp_local import local_source
from serialization.decode.warp_math import project, quad_area, vstack, warp_global


def warp_piecewise(
    image: np.ndarray,
    geometry: PageGeometry,
    detected: dict[int, np.ndarray],
    matrix: np.ndarray,
    anchors: tuple[np.ndarray, np.ndarray],
) -> np.ndarray:
    try:
        inverse = np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        return warp_global(image, matrix, geometry.page_w, geometry.page_h)
    dest, src = _mesh(geometry, detected, inverse, anchors)
    canvas = np.full((geometry.page_h, geometry.page_w, 3), 255, np.uint8)
    filled = np.zeros((geometry.page_h, geometry.page_w), np.uint8)
    rows, cols = dest.shape[:2]
    for row in range(rows - 1):
        for col in range(cols - 1):
            _paste_quad(image, src[row:row + 2, col:col + 2], dest[row:row + 2, col:col + 2], canvas, filled)
    missing = filled == 0
    if bool(missing.any()):
        fallback = warp_global(image, matrix, geometry.page_w, geometry.page_h)
        canvas[missing] = fallback[missing]
    return canvas


def _mesh(
    geometry: PageGeometry,
    detected: dict[int, np.ndarray],
    inverse: np.ndarray,
    anchors: tuple[np.ndarray, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    xs = [0.0, *geometry.tag_xs, float(geometry.page_w - 1)]
    ys = [0.0, *geometry.tag_ys, float(geometry.page_h - 1)]
    placed = {(tag.row, tag.col): tag_center_xy(geometry, tag) for tag in geometry.tags}
    ideal, observed = _known_points(geometry, detected, anchors)
    limit = _node_limit(geometry)
    dest = np.zeros((len(ys), len(xs), 2), np.float32)
    src = np.zeros_like(dest)
    for row, y in enumerate(ys):
        for col, x in enumerate(xs):
            point = np.array(placed.get((row - 1, col - 1), (x, y)), np.float32)
            dest[row, col] = point
            src[row, col] = _node_source(geometry, detected, inverse, row - 1, col - 1, point, ideal, observed, limit)
    return dest, src


def _known_points(
    geometry: PageGeometry,
    detected: dict[int, np.ndarray],
    anchors: tuple[np.ndarray, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    found = [tag for tag in geometry.tags if tag.tag_id in detected]
    ideal = np.array([tag_center_xy(geometry, tag) for tag in found], np.float32).reshape(-1, 2)
    observed = np.array([detected[tag.tag_id] for tag in found], np.float32).reshape(-1, 2)
    anchor_observed, anchor_ideal = anchors
    return vstack(ideal, anchor_ideal), vstack(observed, anchor_observed)


def _node_limit(geometry: PageGeometry) -> float:
    pitches = [b - a for a, b in zip(geometry.tag_xs, geometry.tag_xs[1:])]
    pitches += [b - a for a, b in zip(geometry.tag_ys, geometry.tag_ys[1:])]
    return 0.5 * min(pitches) if pitches else float(geometry.cell)


def _node_source(
    geometry: PageGeometry,
    detected: dict[int, np.ndarray],
    inverse: np.ndarray,
    tag_row: int,
    tag_col: int,
    dest: np.ndarray,
    ideal: np.ndarray,
    observed: np.ndarray,
    limit: float,
) -> np.ndarray:
    if 0 <= tag_row < geometry.tag_rows and 0 <= tag_col < geometry.tag_cols:
        tag_id = tag_row * geometry.tag_cols + tag_col
        if tag_id in detected:
            return np.asarray(detected[tag_id], np.float32)
        return local_source(ideal, observed, dest, inverse, limit)
    return project(inverse, dest)


def _paste_quad(
    image: np.ndarray,
    src_quad: np.ndarray,
    dest_quad: np.ndarray,
    canvas: np.ndarray,
    filled: np.ndarray,
) -> None:
    src = np.array([src_quad[0, 0], src_quad[0, 1], src_quad[1, 1], src_quad[1, 0]], np.float32)
    dst = np.array([dest_quad[0, 0], dest_quad[0, 1], dest_quad[1, 1], dest_quad[1, 0]], np.float32)
    if quad_area(src) < 4.0 or quad_area(dst) < 4.0:
        return
    x0 = max(0, int(np.floor(dst[:, 0].min())) - 1)
    y0 = max(0, int(np.floor(dst[:, 1].min())) - 1)
    x1 = min(canvas.shape[1], int(np.ceil(dst[:, 0].max())) + 2)
    y1 = min(canvas.shape[0], int(np.ceil(dst[:, 1].max())) + 2)
    if x1 <= x0 or y1 <= y0:
        return
    local = cv2.getPerspectiveTransform(src, dst)
    shift = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]], np.float64)
    warped = cv2.warpPerspective(
        image, shift @ local, (x1 - x0, y1 - y0),
        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255),
    )
    poly = np.round(dst - np.array([x0, y0], np.float32)).astype(np.int32)
    mask = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillConvexPoly(mask, poly, 255)
    selected = mask > 0
    canvas[y0:y1, x0:x1][selected] = warped[selected]
    filled[y0:y1, x0:x1][selected] = 1
