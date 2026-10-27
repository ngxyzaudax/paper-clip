import cv2
import numpy as np

from common.geometry import PageGeometry

_CELL_PX = 16


def model_cell_grid(
    model: object, image: np.ndarray, geometry: PageGeometry, num_symbols: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    cell = geometry.cell
    y0 = geometry.origin_y
    x0 = geometry.origin_x
    crop = image[y0:y0 + geometry.rows * cell, x0:x0 + geometry.cols * cell]
    resized = cv2.resize(crop, (geometry.cols * _CELL_PX, geometry.rows * _CELL_PX), interpolation=cv2.INTER_AREA)
    batch = resized.astype(np.float32)[None] / 255.0
    logits, offset = _forward(model, batch)
    used = logits[0, :, :, :num_symbols]
    shifted = used - np.max(used, axis=-1, keepdims=True)
    exp = np.exp(shifted)
    probs = exp / np.sum(exp, axis=-1, keepdims=True)
    symbols = np.argmax(probs, axis=-1).astype(np.int32)
    confidence = np.max(probs, axis=-1).astype(np.float32)
    mean_offset = None
    if offset is not None:
        data_row = min(geometry.header_h // geometry.cell, max(0, offset.shape[1] - 1))
        mean_offset = np.mean(offset[0, data_row:], axis=(0, 1)).astype(np.float32)
    return symbols, confidence, mean_offset


def _forward(model: object, batch: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
    predict = getattr(model, "predict", None)
    output = predict(batch, verbose=0) if predict is not None else model(batch, training=False)
    if isinstance(output, dict):
        logits = np.asarray(output["logits"])
        offset = np.asarray(output["offset"]) if "offset" in output else None
        return logits, offset
    if isinstance(output, (list, tuple)):
        logits = np.asarray(output[0])
        offset = np.asarray(output[1]) if len(output) > 1 else None
        return logits, offset
    return np.asarray(output), None
