import cv2
import numpy as np


def apply_photometric(
    image: np.ndarray,
    brightness: float,
    contrast: float,
    gamma: float,
    gain: tuple[float, float, float],
    mix: float,
) -> np.ndarray:
    colour = image.astype(np.float32)
    colour = (colour - 127.5) * contrast + 127.5
    colour *= np.array(gain, np.float32).reshape(1, 1, 3) * brightness
    if mix > 1e-4:
        red, green, blue = colour[:, :, 0], colour[:, :, 1], colour[:, :, 2]
        colour[:, :, 0] = red * (1 - mix) + green * mix
        colour[:, :, 1] = green * (1 - mix * 0.5) + blue * mix * 0.5
        colour[:, :, 2] = blue * (1 - mix) + red * mix * 0.35
    colour = np.clip(colour, 0, 255)
    if abs(gamma - 1.0) > 1e-3:
        colour = 255.0 * np.power(colour / 255.0, gamma)
    return np.clip(colour, 0, 255).astype(np.uint8)


def apply_noise(image: np.ndarray, sigma: float, rng: np.random.Generator) -> np.ndarray:
    if sigma <= 0:
        return image
    noise = rng.normal(0.0, sigma, image.shape).astype(np.float32)
    return np.clip(image.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def apply_streaks(image: np.ndarray, strength: float, rng: np.random.Generator) -> np.ndarray:
    if strength <= 0.02:
        return image
    colour = image.astype(np.float32)
    height, width = colour.shape[:2]
    gradient = 1.0 + strength * 0.08 * (np.linspace(-0.5, 0.5, width, dtype=np.float32))
    colour *= gradient.reshape(1, width, 1)
    row_count = max(1, int(strength * 6))
    for row in rng.integers(0, height, size=row_count):
        colour[int(row)] *= 1.0 - 0.18 * strength
    return np.clip(colour, 0, 255).astype(np.uint8)


def jpeg_roundtrip(image: np.ndarray, quality: int) -> np.ndarray:
    if quality >= 100:
        return image
    ok, encoded = cv2.imencode(
        ".jpg", cv2.cvtColor(image, cv2.COLOR_RGB2BGR), [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)],
    )
    if not ok:
        return image
    decoded = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    return cv2.cvtColor(decoded, cv2.COLOR_BGR2RGB)
