import numpy as np

from common.config import PaperClipConfig
from common.geometry import PageGeometry
from common.types import Region
from serialization.decode.nearest_colour import blank_and_palette, rgb_to_lab
from serialization.decode.sample_cells import median_rgb, sample_radius, strip_points

STRIP_REJECT_DELTA = 15.0


def calibration_offset_and_refs(
    image: np.ndarray, geometry: PageGeometry, config: PaperClipConfig,
) -> tuple[int, int, np.ndarray]:
    ideal = np.asarray(blank_and_palette(config), np.float32)
    radius = sample_radius(geometry.cell, config.dot_ratio)
    scored = [
        _measure(image, geometry, slot.calibration, config.num_symbols, ideal, radius)
        for slot in geometry.slots
    ]
    return 0, 0, _average(_kept(scored))


def _measure(
    image: np.ndarray,
    geometry: PageGeometry,
    region: Region,
    num_symbols: int,
    ideal: np.ndarray,
    radius: int,
) -> tuple[float, np.ndarray]:
    ideal_lab = rgb_to_lab(ideal)
    scores = {
        (dx, dy): _score(image, geometry, region, num_symbols, dx, dy, radius, ideal_lab)
        for dy in range(-6, 7)
        for dx in range(-6, 7)
    }
    best = min(scores.values())
    good = [offset for offset, score in scores.items() if score <= best + 1.0]
    dx = int(round(sum(item[0] for item in good) / len(good)))
    dy = int(round(sum(item[1] for item in good) / len(good)))
    return best, _references(image, geometry, region, num_symbols, dx, dy, radius, ideal)


def _score(
    image: np.ndarray,
    geometry: PageGeometry,
    region: Region,
    num_symbols: int,
    dx: int,
    dy: int,
    radius: int,
    ideal_lab: np.ndarray,
) -> float:
    symbols, xs, ys = strip_points(geometry, region, num_symbols, dx, dy)
    samples = rgb_to_lab(median_rgb(image, xs, ys, radius))
    dists = np.linalg.norm(samples - ideal_lab[symbols], axis=1)
    return float(np.mean(dists))


def _references(
    image: np.ndarray,
    geometry: PageGeometry,
    region: Region,
    num_symbols: int,
    dx: int,
    dy: int,
    radius: int,
    ideal: np.ndarray,
) -> np.ndarray:
    symbols, xs, ys = strip_points(geometry, region, num_symbols, dx, dy)
    samples = median_rgb(image, xs, ys, radius)
    refs = ideal.copy()
    for symbol in range(num_symbols):
        chosen = samples[symbols == symbol]
        if len(chosen):
            refs[symbol] = np.mean(chosen, axis=0)
    return refs


def _kept(scored: list[tuple[float, np.ndarray]]) -> list[np.ndarray]:
    best = min(score for score, _refs in scored)
    return [refs for score, refs in scored if score <= best + STRIP_REJECT_DELTA]


def _average(refs: list[np.ndarray]) -> np.ndarray:
    return np.mean(np.stack(refs), axis=0)
