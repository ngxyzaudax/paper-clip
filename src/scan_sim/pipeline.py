from typing import NamedTuple

import numpy as np

from scan_sim.ink import apply_ink_bleed, apply_optical_blur
from scan_sim.photometric import apply_noise, apply_photometric, apply_streaks, jpeg_roundtrip
from scan_sim.warp import apply_perspective, apply_rotation, apply_sine_warp, crop_edges


class AugmentLevels(NamedTuple):
    bleed_mm: float
    blur_mm: float
    brightness: float
    contrast: float
    gamma: float
    noise_sigma: float
    jpeg_quality: int
    rotation_deg: float
    perspective: float
    warp_mm: float
    gain: tuple[float, float, float]
    mix: float
    clip_mm: float
    streak: float


def levels_for_strength(strength: float) -> AugmentLevels:
    scale = float(np.clip(strength, 0.0, 1.0))
    return AugmentLevels(
        bleed_mm=scale * 0.18,
        blur_mm=scale * 0.12,
        brightness=1.0 + scale * 0.16,
        contrast=1.0 + scale * 0.22,
        gamma=1.0 + scale * 0.30,
        noise_sigma=scale * 5.0,
        jpeg_quality=101 if scale <= 0 else int(round(94 - scale * 38)),
        rotation_deg=scale * 6.0,
        perspective=scale,
        warp_mm=scale * 0.9,
        gain=(1.0 + scale * 0.12, 1.0 - scale * 0.08, 1.0 + scale * 0.05),
        mix=scale * 0.08,
        clip_mm=scale * 4.0,
        streak=scale,
    )


def apply_scan_augment(
    image: np.ndarray, strength: float, dpi: int, rng: np.random.Generator,
) -> np.ndarray:
    if strength <= 0:
        return image.copy()
    levels = levels_for_strength(strength)
    page = apply_appearance(image, levels, dpi, rng)
    page = crop_edges(page, levels.clip_mm, dpi)
    page = apply_sine_warp(page, levels.warp_mm, dpi)
    page = apply_perspective(page, levels.perspective, rng)
    sign = -1.0 if rng.random() < 0.5 else 1.0
    page = apply_rotation(page, sign * levels.rotation_deg)
    return jpeg_roundtrip(page, levels.jpeg_quality)


def apply_appearance(
    image: np.ndarray, levels: AugmentLevels, dpi: int, rng: np.random.Generator,
) -> np.ndarray:
    page = apply_ink_bleed(image, levels.bleed_mm, dpi)
    page = apply_photometric(
        page, levels.brightness, levels.contrast, levels.gamma, levels.gain, levels.mix,
    )
    page = apply_optical_blur(page, levels.blur_mm, dpi)
    page = apply_noise(page, levels.noise_sigma, rng)
    return apply_streaks(page, levels.streak, rng)


def apply_colour_cast(image: np.ndarray, strength: float, rng: np.random.Generator) -> np.ndarray:
    del rng
    levels = levels_for_strength(max(strength, 0.0))
    return apply_photometric(image, 1.0, 1.0, 1.0, levels.gain, max(levels.mix, 0.12))
