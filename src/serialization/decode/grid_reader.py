import numpy as np

from common.config import PaperClipConfig, center_sample_half
from common.page_layout import data_grid_region, grid_dimensions, margin_offset
from common.types import SymbolGrid


def locate_data_grid(
    image: np.ndarray, config: PaperClipConfig, dx: int = 0, dy: int = 0
) -> np.ndarray:
    mx, my = margin_offset(config)
    region = data_grid_region(config)
    x0 = mx + region.x + dx
    y0 = my + region.y + dy
    return image[y0 : y0 + region.height, x0 : x0 + region.width]


def sample_cells_vectorized(
    grid_region: np.ndarray, config: PaperClipConfig
) -> np.ndarray:
    cell = config.cell_size_px
    s = center_sample_half(cell)
    c = cell // 2
    cols, rows = grid_dimensions(config)
    trimmed = grid_region[: rows * cell, : cols * cell].astype(np.float32)
    reshaped = trimmed.reshape(rows, cell, cols, cell, 3)
    y_lo = max(0, c - s)
    y_hi = min(cell, c + s + 1)
    x_lo = max(0, c - s)
    x_hi = min(cell, c + s + 1)
    inner = reshaped[:, y_lo:y_hi, :, x_lo:x_hi, :]
    win_h = y_hi - y_lo
    win_w = x_hi - x_lo
    inner_t = inner.transpose(0, 2, 1, 3, 4).reshape(rows, cols, win_h * win_w, 3)
    brightness = inner_t.sum(axis=-1)
    min_idx = np.argmin(brightness, axis=2)
    r_idx = np.arange(rows)[:, None]
    c_idx = np.arange(cols)[None, :]
    darkest = inner_t[r_idx, c_idx, min_idx]
    return darkest[:, :, ::-1].copy()


def classify_cells_vectorized(
    cell_averages: np.ndarray,
    reference_rgbs: np.ndarray,
) -> SymbolGrid:
    rows, cols, _ = cell_averages.shape
    flat_cells = cell_averages.reshape(-1, 3).astype(np.float32)
    flat_refs = reference_rgbs.reshape(-1, 3).astype(np.float32)
    num_refs = flat_refs.shape[0]
    best_idx = np.zeros(flat_cells.shape[0], dtype=np.int32)
    best_dist = np.full(flat_cells.shape[0], np.inf, dtype=np.float32)
    for i in range(num_refs):
        d = ((flat_cells - flat_refs[i]) ** 2).sum(axis=1)
        closer = d < best_dist
        best_idx[closer] = i
        best_dist[closer] = d[closer]
    return best_idx.reshape(rows, cols).tolist()


def classify_cells_ml(
    grid_region: np.ndarray,
    config: PaperClipConfig,
    model: "tf.keras.Model",
) -> tuple[SymbolGrid, np.ndarray]:
    cell = config.cell_size_px
    cols, rows = grid_dimensions(config)
    trimmed = grid_region[: rows * cell, : cols * cell]
    reshaped = trimmed.reshape(rows, cell, cols, cell, 3)
    crops = reshaped.transpose(0, 2, 1, 3, 4).reshape(rows * cols, cell, cell, 3)
    crops_rgb = crops[:, :, ::-1].astype(np.float32)
    predictions = model.predict(crops_rgb, batch_size=512, verbose=0)
    labels = np.argmax(predictions, axis=1)
    confidences = np.max(predictions, axis=1)
    grid = labels.reshape(rows, cols).tolist()
    conf_grid = confidences.reshape(rows, cols)
    return grid, conf_grid
