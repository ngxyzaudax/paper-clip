import numpy as np

from common.config import CALIBRATION_BAR_ROWS, PaperClipConfig, center_sample_half
from common.page_layout import calibration_region, margin_offset
from common.symbols import symbol_count


def _darkest_pixel_color(
    image: np.ndarray, x: int, y: int, cell_size: int,
) -> np.ndarray:
    s = center_sample_half(cell_size)
    cx = x + cell_size // 2
    cy = y + cell_size // 2
    region = image[cy - s : cy + s + 1, cx - s : cx + s + 1]
    if region.size == 0:
        return np.array([255, 255, 255], dtype=np.float32)
    brightness = region.astype(np.float32).sum(axis=-1)
    min_pos = np.unravel_index(np.argmin(brightness), brightness.shape)
    pix = region[min_pos]
    return np.array([pix[2], pix[1], pix[0]], dtype=np.float32)


def extract_calibration_references(
    image: np.ndarray, config: PaperClipConfig,
) -> np.ndarray:
    """Returns shape (num_symbols, 3) float RGB array of calibration references."""
    mx, my = margin_offset(config)
    region = calibration_region(config)
    cell = config.cell_size_px
    total_symbols = symbol_count(config.num_colors)
    x_base = mx + region.x
    y_base = my + region.y
    accumulators = np.zeros((total_symbols, 3), dtype=np.float64)
    counts = np.zeros(total_symbols, dtype=np.int32)
    for rep in range(CALIBRATION_BAR_ROWS):
        y = y_base + rep * cell
        for sym_idx in range(total_symbols):
            x = x_base + sym_idx * cell
            if y + cell > image.shape[0] or x + cell > image.shape[1]:
                continue
            accumulators[sym_idx] += _darkest_pixel_color(image, x, y, cell)
            counts[sym_idx] += 1
    safe_counts = np.maximum(counts, 1).reshape(-1, 1)
    return (accumulators / safe_counts).astype(np.float32)
