import cv2
import numpy as np

from common.geometry_measure import mm_to_px


def apply_sine_warp(image: np.ndarray, amplitude_mm: float, dpi: int) -> np.ndarray:
    amplitude = float(mm_to_px(amplitude_mm, dpi))
    if amplitude < 0.4:
        return image
    height, width = image.shape[:2]
    ys, xs = np.indices((height, width), dtype=np.float32)
    period_y = max(height * 0.65, 1.0)
    period_x = max(width * 0.7, 1.0)
    map_x = xs + amplitude * np.sin(2 * np.pi * ys / period_y)
    map_y = ys + amplitude * 0.65 * np.sin(2 * np.pi * xs / period_x)
    return cv2.remap(
        image, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255),
    )


def apply_perspective(image: np.ndarray, strength: float, rng: np.random.Generator) -> np.ndarray:
    if strength <= 0:
        return image
    height, width = image.shape[:2]
    jitter = strength * 0.045 * min(height, width)
    src = np.float32([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
    noise = rng.normal(0.0, jitter / 2.0, src.shape).astype(np.float32)
    pad = int(jitter + 8)
    dst = src + noise + pad
    homography = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(
        image, homography, (width + 2 * pad, height + 2 * pad),
        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255),
    )


def apply_rotation(image: np.ndarray, degrees: float) -> np.ndarray:
    if abs(degrees) < 0.05:
        return image
    height, width = image.shape[:2]
    center = ((width - 1) / 2.0, (height - 1) / 2.0)
    matrix = cv2.getRotationMatrix2D(center, degrees, 1.0)
    cosine, sine = abs(float(matrix[0, 0])), abs(float(matrix[0, 1]))
    bound_w = int(height * sine + width * cosine) + 4
    bound_h = int(height * cosine + width * sine) + 4
    matrix[0, 2] += bound_w / 2.0 - center[0]
    matrix[1, 2] += bound_h / 2.0 - center[1]
    return cv2.warpAffine(
        image, matrix, (bound_w, bound_h),
        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255),
    )


def crop_edges(image: np.ndarray, clip_mm: float, dpi: int) -> np.ndarray:
    px = mm_to_px(clip_mm, dpi)
    if px <= 0:
        return image
    height, width = image.shape[:2]
    limit = max(1, min(height, width) // 8)
    px = min(px, limit)
    if height <= 2 * px or width <= 2 * px:
        return image
    return image[px:height - px, px:width - px].copy()


def shift_image(image: np.ndarray, dx: float, dy: float) -> np.ndarray:
    matrix = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(
        image, matrix, (image.shape[1], image.shape[0]),
        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255),
    )
