from collections.abc import Callable

import cv2
import numpy as np

_SPAN = 3200
_MIN_SIDE = 180
_CLOSE = 25
_TURNS = (None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE)

def read_centre[Header](
    image: np.ndarray,
    decode: Callable[[np.ndarray], tuple[Header, np.ndarray | None] | None],
) -> tuple[np.ndarray, Header, np.ndarray] | None:
    window = centre_code_window(image)
    if window is None:
        return None
    x_px, y_px, crop = window
    for turns, code in enumerate(_TURNS):
        found = decode(crop if code is None else cv2.rotate(crop, code))
        if found is None or found[1] is None:
            continue
        header, points = found
        rotated = image if code is None else cv2.rotate(image, code)
        origin = _origin(image.shape, x_px, y_px, crop.shape[1], crop.shape[0], turns)
        return rotated, header, points + origin
    return None


def centre_code_window(image: np.ndarray) -> tuple[int, int, np.ndarray] | None:
    x0, y0, region = _centre_region(image)
    box = _dark_square(region)
    if box is None:
        return None
    left, top, crop = _pad(region, box)
    return x0 + left, y0 + top, crop


def _centre_region(image: np.ndarray) -> tuple[int, int, np.ndarray]:
    height, width = image.shape[:2]
    span = min(height, width, _SPAN)
    x0 = max(0, (width - span) // 2)
    y0 = max(0, (height - span) // 2)
    return x0, y0, image[y0:y0 + span, x0:x0 + span]


def _dark_square(region: np.ndarray) -> tuple[int, int, int, int] | None:
    gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
    mask = cv2.GaussianBlur(gray, (0, 0), 2.5) < 90
    closed = cv2.morphologyEx(
        mask.astype(np.uint8) * 255,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (_CLOSE, _CLOSE)),
    )
    return _squarest(closed, region.shape)


def _squarest(mask: np.ndarray, shape: tuple[int, ...]) -> tuple[int, int, int, int] | None:
    limit = int(min(shape[0], shape[1]) * 0.8)
    boxes = tuple(
        cv2.boundingRect(contour)
        for contour in cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    )
    usable = tuple(box for box in boxes if _usable(int(box[2]), int(box[3]), limit))
    if not usable:
        return None
    x_px, y_px, width, height = max(usable, key=lambda box: int(box[2]) * int(box[3]))
    return int(x_px), int(y_px), int(width), int(height)


def _usable(width: int, height: int, limit: int) -> bool:
    ratio = width / height if height else 0.0
    return _MIN_SIDE <= width < limit and _MIN_SIDE <= height < limit and 0.85 <= ratio <= 1.18


def _origin(
    shape: tuple[int, ...], x_px: int, y_px: int, crop_w: int, crop_h: int, turns: int,
) -> np.ndarray:
    height, width = int(shape[0]), int(shape[1])
    corners = (
        (x_px, y_px),
        (height - (y_px + crop_h), x_px),
        (width - (x_px + crop_w), height - (y_px + crop_h)),
        (y_px, width - (x_px + crop_w)),
    )
    return np.array(corners[turns], np.float32)


def _pad(region: np.ndarray, box: tuple[int, int, int, int]) -> tuple[int, int, np.ndarray]:
    x_px, y_px, width, height = box
    pad = max(48, int(max(width, height) * 0.12))
    left = max(0, x_px - pad)
    top = max(0, y_px - pad)
    right = min(region.shape[1], x_px + width + pad)
    bottom = min(region.shape[0], y_px + height + pad)
    return left, top, region[top:bottom, left:right]
