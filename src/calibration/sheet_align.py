import cv2
import numpy as np

from calibration.sheet_field import tag_centers
from calibration.sheet_spec import Patch, SheetSide
from common.geometry_measure import mm_to_px
from common.geometry_qr import qr_side_px

MIN_PATCH_TAGS = 4


def frame_matrix(side: SheetSide, found: dict[int, np.ndarray]) -> np.ndarray | None:
    pairs = [(tag.x_mm, tag.y_mm, found[tag.tag_id]) for tag in side.frame if tag.tag_id in found]
    if len(pairs) < 4:
        return None
    source = np.array([(x_mm, y_mm) for x_mm, y_mm, _point in pairs], np.float32)
    dest = np.array([point for _x, _y, point in pairs], np.float32)
    matrix, _mask = cv2.findHomography(source, dest, cv2.RANSAC, 2.0)
    return None if matrix is None else np.asarray(matrix, np.float64)


def warp_qr(image: np.ndarray, patch: Patch, matrix: np.ndarray) -> np.ndarray:
    corners = _box(patch.x_mm - 0.6, patch.y_mm - 0.6, patch.w_mm + 1.2, patch.h_mm + 1.2)
    mapped = cv2.perspectiveTransform(corners.reshape(1, -1, 2), matrix).reshape(4, 2)
    side = qr_side_px(720, patch.qr_mm) + mm_to_px(1.2, 720)
    dest = np.array([[0, 0], [side, 0], [side, side], [0, side]], np.float32)
    transform = cv2.getPerspectiveTransform(mapped.astype(np.float32), dest)
    return cv2.warpPerspective(image, transform, (side, side), flags=cv2.INTER_LINEAR)


def warp_patch(image: np.ndarray, patch: Patch, found: dict[int, np.ndarray]) -> np.ndarray | None:
    """Warp the patch onto its 720 dpi layout using only this patch's own detected tags."""
    present = [tag_id for tag_id in patch.tag_ids if tag_id in found]
    if len(present) < MIN_PATCH_TAGS:
        return None
    transform = _fit(patch, found, present)
    if transform is None:
        return None
    size = (mm_to_px(patch.w_mm, 720), mm_to_px(patch.h_mm, 720))
    return cv2.warpPerspective(image, transform, size, flags=cv2.INTER_LINEAR)


def leave_one_out(patch: Patch, found: dict[int, np.ndarray]) -> float:
    """Largest error, in cells, when each detected tag is predicted from the others."""
    present = [tag_id for tag_id in patch.tag_ids if tag_id in found]
    if len(present) < MIN_PATCH_TAGS + 1:
        return 99.0
    errors = [_held_error(patch, found, present, hold) for hold in present]
    return max(errors) / patch.cell_px


def _held_error(patch: Patch, found: dict[int, np.ndarray], present: list[int], hold: int) -> float:
    transform = _fit(patch, found, [tag_id for tag_id in present if tag_id != hold])
    if transform is None:
        return 99.0 * patch.cell_px
    point = np.array([[found[hold]]], np.float64)
    predicted = cv2.perspectiveTransform(point, transform).reshape(2)
    expected = np.array(_local_px(patch, *tag_centers(patch)[hold]))
    return float(np.linalg.norm(predicted - expected))


def _fit(patch: Patch, found: dict[int, np.ndarray], ids: list[int]) -> np.ndarray | None:
    centers = tag_centers(patch)
    source = np.array([found[tag_id] for tag_id in ids], np.float64)
    dest = np.array([_local_px(patch, *centers[tag_id]) for tag_id in ids], np.float64)
    if not _spans_two_per_row([centers[tag_id][1] for tag_id in ids]):
        return _affine(source, dest)
    matrix, _mask = cv2.findHomography(source, dest, 0)
    return None if matrix is None else np.asarray(matrix, np.float64)


def _spans_two_per_row(rows_mm: list[float]) -> bool:
    counts: dict[float, int] = {}
    for row in rows_mm:
        counts[round(row, 3)] = counts.get(round(row, 3), 0) + 1
    return len(counts) >= 2 and min(counts.values()) >= 2


def _affine(source: np.ndarray, dest: np.ndarray) -> np.ndarray | None:
    design = np.hstack([source, np.ones((len(source), 1))])
    solution, _res, rank, _sv = np.linalg.lstsq(design, dest, rcond=None)
    if rank < 3:
        return None
    return np.vstack([solution.T, [0.0, 0.0, 1.0]])


def _local_px(patch: Patch, x_mm: float, y_mm: float) -> tuple[float, float]:
    return float(mm_to_px(x_mm - patch.x_mm, 720)), float(mm_to_px(y_mm - patch.y_mm, 720))


def _box(x_mm: float, y_mm: float, w_mm: float, h_mm: float) -> np.ndarray:
    return np.array(
        [[x_mm, y_mm], [x_mm + w_mm, y_mm], [x_mm + w_mm, y_mm + h_mm], [x_mm, y_mm + h_mm]],
        np.float32,
    )
