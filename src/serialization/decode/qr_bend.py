from collections.abc import Callable

import cv2
import numpy as np

_BENDS = (0.0, -0.02, 0.02, -0.04, 0.04, -0.06, 0.06)
_PAD = 0.6

type Decode = Callable[[str], object | None]


def bent_qr_retry(
    image: np.ndarray, detectors: tuple[object, ...], parse: Decode,
) -> tuple[object, np.ndarray] | None:
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    corners = _locate(bgr, detectors)
    if corners is None:
        return None
    x0, y0, crop = _crop(bgr, corners)
    side = float(max(np.ptp(corners[:, 0]), np.ptp(corners[:, 1])))
    for bend_x, bend_y in sorted(((a, b) for a in _BENDS for b in _BENDS), key=lambda pair: abs(pair[0]) + abs(pair[1])):
        if bend_x == 0.0 and bend_y == 0.0:
            continue
        bent, map_x, map_y = _bend(crop, bend_x * side, bend_y * side)
        for detector in detectors:
            result = detector.detectAndDecode(bent)
            header = parse(str(result[0] or "")) if result else None
            if header is None or len(result) < 2 or result[1] is None:
                continue
            points = np.asarray(result[1], np.float32).reshape(-1, 2)
            return header, _unbend(points, map_x, map_y, x0, y0)
    return None


def _locate(bgr: np.ndarray, detectors: tuple[object, ...]) -> np.ndarray | None:
    for detector in detectors:
        found, points = detector.detect(bgr)
        if found and points is not None:
            return np.asarray(points, np.float32).reshape(-1, 2)
    return None


def _crop(bgr: np.ndarray, corners: np.ndarray) -> tuple[int, int, np.ndarray]:
    low = corners.min(axis=0)
    high = corners.max(axis=0)
    pad = float(np.max(high - low)) * _PAD
    x0, y0 = int(max(0, low[0] - pad)), int(max(0, low[1] - pad))
    x1 = int(min(bgr.shape[1], high[0] + pad))
    y1 = int(min(bgr.shape[0], high[1] + pad))
    return x0, y0, bgr[y0:y1, x0:x1]


def _bend(crop: np.ndarray, shift_x: float, shift_y: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    height, width = crop.shape[:2]
    ys, xs = np.indices((height, width), dtype=np.float32)
    u = (xs - width / 2.0) / max(width / 2.0, 1.0)
    v = (ys - height / 2.0) / max(height / 2.0, 1.0)
    map_x = xs + shift_x * v * v
    map_y = ys + shift_y * u * u
    bent = cv2.remap(crop, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return bent, map_x, map_y


def _unbend(points: np.ndarray, map_x: np.ndarray, map_y: np.ndarray, x0: int, y0: int) -> np.ndarray:
    height, width = map_x.shape
    cols = np.clip(np.round(points[:, 0]).astype(int), 0, width - 1)
    rows = np.clip(np.round(points[:, 1]).astype(int), 0, height - 1)
    return np.stack([map_x[rows, cols] + x0, map_y[rows, cols] + y0], axis=1).astype(np.float32)
