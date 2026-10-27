import numpy as np

from common.config import PaperClipConfig
from common.geometry import PageGeometry
from serialization.decode.nearest_colour import nearest_symbols
from serialization.decode.sample_cells import cell_centers, median_rgb, sample_radius


def classify_cells(
    image: np.ndarray,
    geometry: PageGeometry,
    config: PaperClipConfig,
    dx: int,
    dy: int,
    references: np.ndarray,
    model: object | None,
    cells: list[tuple[int, int]],
    colour_image: np.ndarray | None = None,
) -> tuple[list[int], list[float]]:
    shift_x, shift_y = dx, dy
    if model is not None:
        from serialization.decode.model_classify import mean_cell_offset, model_cell_grid

        predicted, predicted_conf, offset_map = model_cell_grid(model, image, geometry, config.num_symbols)
        offset = None if offset_map is None else mean_cell_offset(offset_map, cells)
        if offset is not None:
            shift_x += int(round(float(offset[0]) * geometry.cell))
            shift_y += int(round(float(offset[1]) * geometry.cell))
    else:
        predicted = None
        predicted_conf = None
    if predicted is not None and predicted.shape[:2] != (geometry.rows, geometry.cols):
        predicted = None
    xs, ys = cell_centers(geometry, cells, shift_x, shift_y)
    sampled = image if colour_image is None else colour_image
    colour_sym, colour_conf = nearest_symbols(median_rgb(sampled, xs, ys, sample_radius(geometry.cell)), references)
    symbols: list[int] = []
    confidence: list[float] = []
    for index, (row, col) in enumerate(cells):
        if predicted is not None and float(predicted_conf[row, col]) >= 0.55:
            symbols.append(int(predicted[row, col]))
            confidence.append(float(predicted_conf[row, col]))
        else:
            symbols.append(int(colour_sym[index]))
            confidence.append(float(colour_conf[index]))
    return symbols, confidence
