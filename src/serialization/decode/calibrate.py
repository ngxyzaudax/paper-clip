import numpy as np

from common.config import PaperClipConfig
from common.geometry import PageGeometry
from serialization.decode.nearest_colour import blank_and_palette, rgb_to_lab
from serialization.decode.sample_cells import calibration_points, median_rgb, sample_radius


def calibration_offset_and_refs(
    image: np.ndarray, geometry: PageGeometry, config: PaperClipConfig,
) -> tuple[int, int, np.ndarray]:
    ideal = np.asarray(blank_and_palette(config), np.float32)
    ideal_lab = rgb_to_lab(ideal)
    radius = sample_radius(geometry.cell)
    strip_dx, strip_dy = _strip_shift(image, geometry, config.num_symbols, radius, ideal_lab)
    refs = _references(image, geometry, config.num_symbols, strip_dx, strip_dy, radius, ideal)
    return 0, 0, refs


def _strip_shift(
    image: np.ndarray,
    geometry: PageGeometry,
    num_symbols: int,
    radius: int,
    ideal_lab: np.ndarray,
) -> tuple[int, int]:
    scores = {
        (dx, dy): _score(image, geometry, num_symbols, dx, dy, radius, ideal_lab)
        for dy in range(-6, 7)
        for dx in range(-6, 7)
    }
    best = min(scores.values())
    good = [offset for offset, score in scores.items() if score <= best + 1.0]
    dx = int(round(sum(item[0] for item in good) / len(good)))
    dy = int(round(sum(item[1] for item in good) / len(good)))
    return dx, dy


def _score(
    image: np.ndarray,
    geometry: PageGeometry,
    num_symbols: int,
    dx: int,
    dy: int,
    radius: int,
    ideal_lab: np.ndarray,
) -> float:
    symbols, xs, ys = calibration_points(geometry, num_symbols, dx, dy)
    samples = rgb_to_lab(median_rgb(image, xs, ys, radius))
    dists = np.linalg.norm(samples - ideal_lab[symbols], axis=1)
    return float(np.mean(dists))


def _references(
    image: np.ndarray,
    geometry: PageGeometry,
    num_symbols: int,
    dx: int,
    dy: int,
    radius: int,
    ideal: np.ndarray,
) -> np.ndarray:
    symbols, xs, ys = calibration_points(geometry, num_symbols, dx, dy)
    samples = median_rgb(image, xs, ys, radius)
    refs = ideal.copy()
    for symbol in range(num_symbols):
        chosen = samples[symbols == symbol]
        if len(chosen):
            refs[symbol] = np.mean(chosen, axis=0)
    return refs
