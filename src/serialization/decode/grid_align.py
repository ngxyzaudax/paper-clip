import cv2
import numpy as np

from common.geometry import PageGeometry

_SHIFT_LIMIT = 0.35
_SPIKE = 0.45
_SMOOTH = 3.0
_MIN_SPREAD = 0.02


def refined_cell_grid(
    model: object,
    image: np.ndarray,
    geometry: PageGeometry,
    num_symbols: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """Read the grid, then read it again after undoing the per-cell shift the model measured."""
    from serialization.decode.model_classify import model_cell_grid

    predicted, confidence, offset = model_cell_grid(model, image, geometry, num_symbols)
    if not _worth_aligning(offset, geometry):
        return predicted, confidence, offset
    second, second_conf, _again = model_cell_grid(
        model, align_grid(image, geometry, offset), geometry, num_symbols,
    )
    if second.shape[:2] != (geometry.rows, geometry.cols):
        return predicted, confidence, offset
    return second, second_conf, offset


def align_grid(image: np.ndarray, geometry: PageGeometry, offset: np.ndarray) -> np.ndarray:
    """Shift each grid pixel back by the measured dot offset, in cell fractions."""
    field = _smooth(offset)
    cell = geometry.cell
    y0, x0 = geometry.origin_y, geometry.origin_x
    height, width = geometry.rows * cell, geometry.cols * cell
    y1, x1 = min(image.shape[0], y0 + height), min(image.shape[1], x0 + width)
    if y1 <= y0 or x1 <= x0:
        return image
    local = cv2.resize(field, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR)
    yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0]
    map_x = (x0 + xx + local[:, :, 0] * cell).astype(np.float32)
    map_y = (y0 + yy + local[:, :, 1] * cell).astype(np.float32)
    moved = image.copy()
    moved[y0:y1, x0:x1] = cv2.remap(
        image, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT,
    )
    return moved


def _worth_aligning(offset: np.ndarray | None, geometry: PageGeometry) -> bool:
    if offset is None or offset.shape[:2] != (geometry.rows, geometry.cols):
        return False
    return float(np.std(offset)) >= _MIN_SPREAD


def _smooth(offset: np.ndarray) -> np.ndarray:
    field = np.asarray(offset, np.float32).copy()
    field[np.linalg.norm(field, axis=-1) > _SPIKE] = 0.0
    return np.clip(cv2.GaussianBlur(field, (0, 0), _SMOOTH), -_SHIFT_LIMIT, _SHIFT_LIMIT)
