import cv2
import numpy as np

from common.geometry import PageGeometry
from serialization.decode.model_batch import forward_grid
from serialization.decode.model_strips import CELL_PX


def model_cell_grid(
    model: object, image: np.ndarray, geometry: PageGeometry, num_symbols: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    cell = geometry.cell
    y0 = geometry.origin_y
    x0 = geometry.origin_x
    crop = image[y0:y0 + geometry.rows * cell, x0:x0 + geometry.cols * cell]
    resized = cv2.resize(crop, (geometry.cols * CELL_PX, geometry.rows * CELL_PX), interpolation=cv2.INTER_AREA)
    logits, offset = forward_grid(model, resized.astype(np.float32) / 255.0)
    return _read(logits, offset, num_symbols)


def _read(
    logits: np.ndarray, offset: np.ndarray | None, num_symbols: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    used = logits[:, :, :num_symbols]
    shifted = used - np.max(used, axis=-1, keepdims=True)
    exp = np.exp(shifted)
    probs = exp / np.sum(exp, axis=-1, keepdims=True)
    symbols = np.argmax(probs, axis=-1).astype(np.int32)
    confidence = np.max(probs, axis=-1).astype(np.float32)
    return symbols, confidence, None if offset is None else offset.astype(np.float32)


def mean_cell_offset(offset: np.ndarray, cells: list[tuple[int, int]]) -> np.ndarray | None:
    inside = [(row, col) for row, col in cells if row < offset.shape[0] and col < offset.shape[1]]
    if not inside:
        return None
    rows = np.fromiter((row for row, _ in inside), np.int64, len(inside))
    cols = np.fromiter((col for _, col in inside), np.int64, len(inside))
    return np.mean(offset[rows, cols], axis=0).astype(np.float32)

