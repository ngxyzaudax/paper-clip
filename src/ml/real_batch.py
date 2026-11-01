from typing import NamedTuple

import numpy as np

from ml.network import CELL_PX
from scan_sim.warp import shift_image

_GRID = 6
_HALO = 1


class RealPage(NamedTuple):
    image: np.ndarray
    labels: np.ndarray
    train_origins: np.ndarray
    held_origins: np.ndarray


def prepare_page(image: np.ndarray, labels: np.ndarray, grid: int = _GRID) -> RealPage:
    origins = _origins(labels, grid)
    split = int(labels.shape[0] * 0.85)
    train = origins[origins[:, 0] + grid <= split] if len(origins) else origins
    held = origins[origins[:, 0] >= split] if len(origins) else origins
    if len(train) == 0:
        train = origins
    return RealPage(image, labels, train, held)


def sample_real_batch(
    pages: list[RealPage],
    batch_size: int,
    rng: np.random.Generator,
    grid: int = _GRID,
    held: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    images = np.empty((batch_size, grid * CELL_PX, grid * CELL_PX, 3), np.float32)
    labels = np.empty((batch_size, grid, grid), np.int32)
    offsets = np.empty((batch_size, grid, grid, 2), np.float32)
    for index in range(batch_size):
        page = pages[int(rng.integers(0, len(pages)))]
        images[index], labels[index], offsets[index] = _one(page, rng, grid, held)
    return images, labels, offsets


def _one(
    page: RealPage, rng: np.random.Generator, grid: int, held: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    pool = _pool(page, held)
    origin = pool[int(rng.integers(0, len(pool)))]
    shift = rng.uniform(-0.22, 0.22, size=2).astype(np.float32)
    return _crop(page, origin, shift, grid, rng)


def _pool(page: RealPage, held: bool) -> np.ndarray:
    chosen = page.held_origins if held and len(page.held_origins) else page.train_origins
    return chosen if len(chosen) else page.held_origins


def _crop(
    page: RealPage,
    origin: np.ndarray,
    shift: np.ndarray,
    grid: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    row, col = int(origin[0]), int(origin[1])
    patch = _patch(page.image, row - _HALO, col - _HALO, grid + 2 * _HALO)
    moved = shift_image(patch, float(shift[0]) * CELL_PX, float(shift[1]) * CELL_PX)
    view = moved[CELL_PX:CELL_PX + grid * CELL_PX, CELL_PX:CELL_PX + grid * CELL_PX]
    symbols = page.labels[row:row + grid, col:col + grid].astype(np.int32)
    offset = np.broadcast_to(shift, (grid, grid, 2)).astype(np.float32).copy()
    return _jitter(view, rng), symbols, offset


def _patch(image: np.ndarray, row: int, col: int, cells: int) -> np.ndarray:
    side = cells * CELL_PX
    y_px, x_px = row * CELL_PX, col * CELL_PX
    return image[y_px:y_px + side, x_px:x_px + side]


def _jitter(image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    gain = float(rng.uniform(0.9, 1.1))
    bias = float(rng.uniform(-8.0, 8.0))
    return np.clip(image.astype(np.float32) * gain + bias, 0, 255) / 255.0


def _origins(labels: np.ndarray, grid: int) -> np.ndarray:
    valid = (labels >= 0).astype(np.int32)
    prefix = np.pad(valid, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    side = grid + 2 * _HALO
    row_end = labels.shape[0] - side + 1
    col_end = labels.shape[1] - side + 1
    if row_end <= 0 or col_end <= 0:
        return np.zeros((0, 2), np.int32)
    rows, cols = np.meshgrid(np.arange(row_end), np.arange(col_end), indexing="ij")
    total = prefix[rows + side, cols + side] - prefix[rows, cols + side] - prefix[rows + side, cols] + prefix[rows, cols]
    keep = total == side * side
    return np.stack([rows[keep] + _HALO, cols[keep] + _HALO], axis=1).astype(np.int32)
