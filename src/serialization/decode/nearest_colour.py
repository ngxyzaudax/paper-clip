import numpy as np

from common.palette import palette_from_config
from common.config import PaperClipConfig
from common.types import RGB

_XN, _YN, _ZN = 0.95047, 1.0, 1.08883


def blank_and_palette(config: PaperClipConfig) -> list[RGB]:
    return [(255, 255, 255), *palette_from_config(config)]


def nearest_symbols(samples: np.ndarray, references: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    labs = rgb_to_lab(samples)
    refs = rgb_to_lab(references)
    dists = np.linalg.norm(labs[:, None, :] - refs[None, :, :], axis=2)
    best = np.argmin(dists, axis=1)
    best_d = dists[np.arange(len(samples)), best]
    masked = dists.copy()
    masked[np.arange(len(samples)), best] = np.inf
    second = np.min(masked, axis=1)
    gap = np.maximum(0.0, second - best_d)
    confidence = gap / (gap + best_d + 1e-3)
    confidence = np.where(best_d > 36.0, confidence * 0.25, confidence)
    return best.astype(np.int32), confidence.astype(np.float32)


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    colour = np.asarray(rgb, np.float32) / 255.0
    linear = np.where(colour <= 0.04045, colour / 12.92, ((colour + 0.055) / 1.055) ** 2.4)
    matrix = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ], np.float32)
    xyz = linear @ matrix.T
    xyz = xyz / np.array([_XN, _YN, _ZN], np.float32)
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16.0 / 116.0)
    lab = np.empty_like(f)
    lab[:, 0] = 116.0 * f[:, 1] - 16.0
    lab[:, 1] = 500.0 * (f[:, 0] - f[:, 1])
    lab[:, 2] = 200.0 * (f[:, 1] - f[:, 2])
    return lab
