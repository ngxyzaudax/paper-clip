import cv2
import numpy as np

_LEVELS = (100, 110, 120, 130, 140, 150)


def binary_views(image: np.ndarray) -> tuple[np.ndarray, ...]:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return tuple(_view(gray, level) for level in _LEVELS)


def _view(gray: np.ndarray, level: int) -> np.ndarray:
    ink = np.where(gray < level, 0, 255).astype(np.uint8)
    return cv2.cvtColor(ink, cv2.COLOR_GRAY2RGB)
