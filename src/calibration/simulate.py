import numpy as np

from scan_sim.pipeline import apply_scan_augment


def ink_scans(
    images: list[np.ndarray], dpi: int, strength: float, seed: int,
) -> list[np.ndarray]:
    if strength <= 0:
        return [image.copy() for image in images]
    return [
        apply_scan_augment(image, strength, dpi, np.random.default_rng(seed + index))
        for index, image in enumerate(images)
    ]
