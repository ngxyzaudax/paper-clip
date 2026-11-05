import numpy as np

from common.geometry import PageGeometry, tag_center_xy
from common.geometry_types import HeaderSlot
from serialization.decode.errors import DecodeError
from serialization.decode.warp_math import homography, order_quad, project, qr_code_corners

_MATCH_PX = 8.0


def matched_qr_anchors(
    src: np.ndarray,
    dst: np.ndarray,
    quads: tuple[np.ndarray, ...],
    geometry: PageGeometry,
) -> tuple[np.ndarray, np.ndarray]:
    empty = (np.zeros((0, 2), np.float32), np.zeros((0, 2), np.float32))
    try:
        inverse = np.linalg.inv(homography(src, dst))
    except np.linalg.LinAlgError:
        return empty
    used: set[int] = set()
    extra_src: list[np.ndarray] = []
    extra_dst: list[np.ndarray] = []
    for points in quads:
        found = _best_slot(points, inverse, geometry, used)
        if found is None:
            continue
        index, pairs = found
        used.add(index)
        extra_src.extend(pairs[0])
        extra_dst.extend(pairs[1])
    if not extra_src:
        return empty
    return np.stack(extra_src).astype(np.float32), np.stack(extra_dst).astype(np.float32)


def fallback_qr_quad(
    quads: tuple[np.ndarray, ...],
    geometry: PageGeometry,
    detected: dict[int, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    best_score: float | None = None
    best: tuple[np.ndarray, np.ndarray] | None = None
    for points in quads:
        ordered = order_quad(points)
        for slot in geometry.slots:
            corners = qr_code_corners(geometry, slot)
            score = _residual(homography(ordered, corners), geometry, detected)
            if best_score is None or score < best_score:
                best_score = score
                best = (ordered, corners)
    if best is None:
        raise DecodeError("no QR quad to anchor the page")
    return best


def _best_slot(
    points: np.ndarray,
    inverse: np.ndarray,
    geometry: PageGeometry,
    used: set[int],
) -> tuple[int, tuple[list[np.ndarray], list[np.ndarray]]] | None:
    best: tuple[int, tuple[list[np.ndarray], list[np.ndarray]]] | None = None
    best_dist: float | None = None
    for index, slot in enumerate(geometry.slots):
        if index in used:
            continue
        pairs = _pairs(points, inverse, geometry, slot)
        if pairs is None:
            continue
        dist = pairs[2]
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best = (index, (pairs[0], pairs[1]))
    return best


def _pairs(
    points: np.ndarray,
    inverse: np.ndarray,
    geometry: PageGeometry,
    slot: HeaderSlot,
) -> tuple[list[np.ndarray], list[np.ndarray], float] | None:
    ideal = qr_code_corners(geometry, slot)
    projected = np.stack([project(inverse, point) for point in ideal])
    taken: set[int] = set()
    src: list[np.ndarray] = []
    dst: list[np.ndarray] = []
    total = 0.0
    for guess, dest in zip(projected, ideal):
        dists = np.linalg.norm(points - guess, axis=1)
        index = int(np.argmin(dists))
        if index in taken or float(dists[index]) > _MATCH_PX:
            return None
        taken.add(index)
        total += float(dists[index])
        src.append(points[index])
        dst.append(dest)
    return src, dst, total


def _residual(matrix: np.ndarray, geometry: PageGeometry, detected: dict[int, np.ndarray]) -> float:
    if not detected:
        return 0.0
    total = 0.0
    count = 0
    for tag in geometry.tags:
        if tag.tag_id not in detected:
            continue
        expected = np.asarray(tag_center_xy(geometry, tag), np.float32)
        total += float(np.linalg.norm(project(matrix, detected[tag.tag_id]) - expected))
        count += 1
    return total if count else 0.0
