import numpy as np
from PIL import Image, ImageDraw

from common.config import resolve_config
from common.drawing import draw_dot_cell
from common.palette import palette_from_config
from ml.network import CELL_PX
from scan_sim.pipeline import apply_appearance, levels_for_strength
from scan_sim.warp import shift_image


def sample_batch(
    batch_size: int, rng: np.random.Generator, grid: int = 6,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    images = np.empty((batch_size, grid * CELL_PX, grid * CELL_PX, 3), np.float32)
    labels = np.empty((batch_size, grid, grid), np.int32)
    offsets = np.empty((batch_size, grid, grid, 2), np.float32)
    for index in range(batch_size):
        image, label, offset = _one_example(rng, grid)
        images[index] = image
        labels[index] = label
        offsets[index] = offset
    return images, labels, offsets


def _one_example(rng: np.random.Generator, grid: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    num_symbols = int(rng.choice([5, 5, 5, 8, 11]))
    config = resolve_config(num_symbols=num_symbols, cell_size_px=32, print_dpi=720, margin_mm=12)
    palette = palette_from_config(config)
    symbols = rng.integers(0, num_symbols, size=(grid, grid), dtype=np.int32)
    canvas = Image.new("RGB", (grid * CELL_PX, grid * CELL_PX), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    for row in range(grid):
        for col in range(grid):
            symbol = int(symbols[row, col])
            colour = None if symbol == 0 else palette[symbol - 1]
            draw_dot_cell(draw, col * CELL_PX, row * CELL_PX, CELL_PX, colour)
    shift = rng.uniform(-0.22, 0.22, size=2).astype(np.float32)
    image = shift_image(np.asarray(canvas), float(shift[0]) * CELL_PX, float(shift[1]) * CELL_PX)
    strength = float(rng.uniform(0.0, 0.85))
    image = apply_appearance(image, levels_for_strength(strength), dpi=360, rng=rng)
    offset = np.broadcast_to(shift, (grid, grid, 2)).astype(np.float32).copy()
    return image.astype(np.float32) / 255.0, symbols, offset
