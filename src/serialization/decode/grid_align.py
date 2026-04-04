import logging

import numpy as np

from common.config import PaperClipConfig
from common.page_layout import data_grid_region, grid_dimensions, margin_offset

logger = logging.getLogger(__name__)

_PROBE_ROWS = 30


def _color_signal_score(
    image: np.ndarray,
    config: PaperClipConfig,
    blank_rgb: np.ndarray,
    dx: int,
    dy: int,
) -> float:
    mx, my = margin_offset(config)
    region = data_grid_region(config)
    cell = config.cell_size_px
    s = max(1, cell // 8)
    c = cell // 2
    cols, _ = grid_dimensions(config)
    x0 = mx + region.x + dx
    y0 = my + region.y + dy
    probe_h = _PROBE_ROWS * cell
    sub = image[y0 : y0 + probe_h, x0 : x0 + cols * cell]
    if sub.shape[0] < probe_h or sub.shape[1] < cols * cell:
        return -1.0
    trimmed = sub.astype(np.float32)
    reshaped = trimmed.reshape(_PROBE_ROWS, cell, cols, cell, 3)
    y_lo, y_hi = max(0, c - s), min(cell, c + s + 1)
    x_lo, x_hi = max(0, c - s), min(cell, c + s + 1)
    inner = reshaped[:, y_lo:y_hi, :, x_lo:x_hi, :]
    cell_means = inner.mean(axis=(1, 3))
    flat_rgb = cell_means[:, :, ::-1].reshape(-1, 3)
    dist_from_blank = ((flat_rgb - blank_rgb) ** 2).sum(axis=1)
    return float(dist_from_blank.sum())


def find_grid_offset(
    image: np.ndarray,
    config: PaperClipConfig,
    calibration_refs: np.ndarray | None = None,
    is_scan: bool = True,
) -> tuple[int, int]:
    if not is_scan:
        return 0, 0
    if calibration_refs is None:
        return 0, 0
    blank_rgb = calibration_refs[0].astype(np.float32)
    max_off = max(3, config.cell_size_px // 2)
    step = max(1, max_off // 5)
    max_up = min(max_off, config.cell_size_px // 3)
    best_score = _color_signal_score(image, config, blank_rgb, 0, 0)
    best_dx, best_dy = 0, 0
    for dy in range(-max_up, max_off + 1, step):
        for dx in range(-max_off, max_off + 1, step):
            if dx == 0 and dy == 0:
                continue
            score = _color_signal_score(image, config, blank_rgb, dx, dy)
            if score > best_score:
                best_score = score
                best_dx, best_dy = dx, dy
    if step > 1:
        for dy in range(best_dy - step, best_dy + step + 1):
            for dx in range(best_dx - step, best_dx + step + 1):
                score = _color_signal_score(image, config, blank_rgb, dx, dy)
                if score > best_score:
                    best_score = score
                    best_dx, best_dy = dx, dy
    if best_dx != 0 or best_dy != 0:
        logger.info("Grid offset refinement: dx=%d, dy=%d", best_dx, best_dy)
    return best_dx, best_dy
