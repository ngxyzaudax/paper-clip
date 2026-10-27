import cv2
import numpy as np

from common.geometry_measure import mm_to_px


def apply_ink_bleed(image: np.ndarray, bleed_mm: float, dpi: int) -> np.ndarray:
    radius = mm_to_px(bleed_mm, dpi) if bleed_mm > 0 else 0
    if radius <= 0:
        return image
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
    dilated = cv2.dilate(image, kernel)
    ink = np.any(image < 245, axis=2)
    spread = cv2.dilate(ink.astype(np.uint8), kernel).astype(bool) & ~ink
    out = image.copy()
    out[spread] = dilated[spread]
    blurred = cv2.GaussianBlur(out, (0, 0), sigmaX=max(0.4, radius * 0.55), sigmaY=max(0.3, radius * 0.28))
    mixed = cv2.addWeighted(out, 0.72, blurred, 0.28, 0)
    warm = mixed.astype(np.int16)
    warm[:, :, 0] = np.clip(warm[:, :, 0] + 2, 0, 255)
    warm[:, :, 2] = np.clip(warm[:, :, 2] - 1, 0, 255)
    return warm.astype(np.uint8)


def apply_optical_blur(image: np.ndarray, blur_mm: float, dpi: int) -> np.ndarray:
    sigma = mm_to_px(blur_mm, dpi) * 0.45 if blur_mm > 0 else 0.0
    if sigma < 0.35:
        return image
    return cv2.GaussianBlur(image, (0, 0), sigmaX=sigma, sigmaY=sigma)
