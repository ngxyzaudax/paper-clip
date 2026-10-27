import numpy as np

from common.drawing import dot_radius_px
from common.geometry import PageGeometry


def sample_radius(cell: int) -> int:
    return max(1, dot_radius_px(cell) // 2)


def median_rgb(image: np.ndarray, xs: np.ndarray, ys: np.ndarray, radius: int) -> np.ndarray:
    height, width = image.shape[:2]
    out = np.empty((len(xs), 3), np.float32)
    for index, (x, y) in enumerate(zip(xs.tolist(), ys.tolist())):
        x0 = max(0, int(x) - radius)
        x1 = min(width, int(x) + radius + 1)
        y0 = max(0, int(y) - radius)
        y1 = min(height, int(y) + radius + 1)
        patch = image[y0:y1, x0:x1]
        out[index] = 255.0 if patch.size == 0 else np.median(patch.reshape(-1, 3), axis=0)
    return out


def cell_centers(
    geometry: PageGeometry, cells: list[tuple[int, int]], dx: int, dy: int,
) -> tuple[np.ndarray, np.ndarray]:
    xs = np.empty(len(cells), np.float32)
    ys = np.empty(len(cells), np.float32)
    half = geometry.cell // 2
    for index, (row, col) in enumerate(cells):
        xs[index] = geometry.origin_x + col * geometry.cell + half + dx
        ys[index] = geometry.origin_y + row * geometry.cell + half + dy
    return xs, ys


def calibration_points(
    geometry: PageGeometry, num_symbols: int, dx: int, dy: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    count = geometry.cal_rows * num_symbols
    xs = np.empty(count, np.float32)
    ys = np.empty(count, np.float32)
    symbols = np.empty(count, np.int32)
    half = geometry.cell // 2
    index = 0
    for row in range(geometry.cal_rows):
        for symbol in range(num_symbols):
            xs[index] = geometry.origin_x + geometry.calibration.x + symbol * geometry.cell + half + dx
            ys[index] = geometry.origin_y + geometry.calibration.y + row * geometry.cell + half + dy
            symbols[index] = symbol
            index += 1
    return symbols, xs, ys
