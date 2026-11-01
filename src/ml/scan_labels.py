import numpy as np

from common.config import PaperClipConfig
from common.geometry_types import PageGeometry
from common.page_layout import valid_cells_ordered
from serialization.decode.nearest_colour import blank_and_palette, nearest_symbols
from serialization.decode.sample_cells import cell_centers


def labels_from_render(
    image: np.ndarray, geometry: PageGeometry, config: PaperClipConfig,
) -> np.ndarray:
    labels = np.full((geometry.rows, geometry.cols), -1, np.int16)
    cells = valid_cells_ordered(config)
    if not cells:
        return labels
    symbols = _symbols_at(image, geometry, cells, config)
    for (row, col), symbol in zip(cells, symbols):
        labels[row, col] = symbol
    return labels


def _symbols_at(
    image: np.ndarray,
    geometry: PageGeometry,
    cells: list[tuple[int, int]],
    config: PaperClipConfig,
) -> list[int]:
    xs, ys = cell_centers(geometry, cells, 0, 0)
    y_px = np.clip(ys.astype(np.int32), 0, image.shape[0] - 1)
    x_px = np.clip(xs.astype(np.int32), 0, image.shape[1] - 1)
    samples = image[y_px, x_px].astype(np.float32)
    symbols, _confidence = nearest_symbols(samples, np.asarray(blank_and_palette(config), np.float32))
    return [int(symbol) for symbol in symbols.tolist()]
