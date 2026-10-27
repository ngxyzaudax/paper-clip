import cv2
import numpy as np

UNSHARP_AMOUNT = 0.75
UNSHARP_SIGMA = 0.7


def restore_page(image: np.ndarray) -> np.ndarray:
    return unsharp_mask(image, UNSHARP_AMOUNT, UNSHARP_SIGMA)


def unsharp_mask(image: np.ndarray, amount: float, sigma: float) -> np.ndarray:
    if amount <= 1e-6 or sigma <= 0.0:
        return image
    colour = image.astype(np.float32)
    blurred = cv2.GaussianBlur(colour, (0, 0), sigmaX=float(sigma), sigmaY=float(sigma))
    sharp = colour * (1.0 + float(amount)) - blurred * float(amount)
    return np.clip(sharp, 0, 255).astype(np.uint8)
