from dataclasses import replace

import numpy as np

from calibration.sheet_field import UNWRITTEN, cell_counts, field_rect, symbol_grid
from calibration.sheet_spec import Patch
from common.config import default_config
from common.geometry_measure import mm_to_px
from serialization.decode.nearest_colour import blank_and_palette, nearest_symbols
from serialization.decode.sample_cells import sample_radius


def dot_accuracy(warped: np.ndarray, patch: Patch) -> tuple[float, bool]:
    expected = symbol_grid(patch)
    read = _read_grid(warped, patch)
    if not expected or not read:
        return 0.0, True
    return _rate(expected, read, 0, 0), _slipped(expected, read)


def _read_grid(warped: np.ndarray, patch: Patch) -> list[list[int]]:
    cols, rows = cell_counts(patch)
    if cols < 1 or rows < 1:
        return []
    samples = np.asarray([_sample(warped, patch, col, row) for row in range(rows) for col in range(cols)])
    colours = _printed_references(samples, symbol_grid(patch), _ideal(patch))
    symbols, _confidence = nearest_symbols(samples, colours)
    return [symbols[row * cols:(row + 1) * cols].tolist() for row in range(rows)]


def _printed_references(samples: np.ndarray, expected: list[list[int]], ideal: np.ndarray) -> np.ndarray:
    labels = np.asarray(expected, np.int32).reshape(-1)
    refs = ideal.copy()
    for symbol in range(len(ideal)):
        chosen = samples[labels == symbol]
        if len(chosen):
            refs[symbol] = chosen.mean(axis=0)
    return refs


def _ideal(patch: Patch) -> np.ndarray:
    colours = blank_and_palette(replace(default_config(), num_symbols=patch.symbols))
    return np.asarray(colours, np.float32)


def _sample(warped: np.ndarray, patch: Patch, col: int, row: int) -> np.ndarray:
    x0, y0, _width, _height = field_rect(patch)
    radius = sample_radius(patch.cell_px, patch.dot_ratio)
    cx = mm_to_px(x0 - patch.x_mm, 720) + col * patch.cell_px + patch.cell_px // 2
    cy = mm_to_px(y0 - patch.y_mm, 720) + row * patch.cell_px + patch.cell_px // 2
    window = warped[max(0, cy - radius):cy + radius + 1, max(0, cx - radius):cx + radius + 1]
    if window.size == 0:
        return np.array([255.0, 255.0, 255.0], np.float32)
    return window.reshape(-1, window.shape[-1]).mean(axis=0)


def _slipped(expected: list[list[int]], read: list[list[int]]) -> bool:
    base = _rate(expected, read, 0, 0)
    shifts = ((dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))
    return any(_rate(expected, read, dy, dx) > base + 0.02 for dy, dx in shifts)


def _rate(expected: list[list[int]], read: list[list[int]], dy: int, dx: int) -> float:
    hits = total = 0
    for row, line in enumerate(expected):
        for col, symbol in enumerate(line):
            src_row, src_col = row + dy, col + dx
            if not _comparable(expected, symbol, src_row, src_col):
                continue
            total += 1
            hits += int(symbol == read[src_row][src_col])
    return hits / total if total else 0.0


def _comparable(expected: list[list[int]], symbol: int, row: int, col: int) -> bool:
    if symbol == UNWRITTEN or row < 0 or col < 0 or row >= len(expected) or col >= len(expected[0]):
        return False
    return expected[row][col] != UNWRITTEN
