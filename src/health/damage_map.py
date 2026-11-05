import numpy as np

from health.page_cells import page_cell_grid
from serialization.encode.qr_header import DecodedQrHeader

MAP_ROWS = 8
MAP_COLS = 6

DamageMap = tuple[tuple[float, ...], ...]


def page_damage_map(wrong: np.ndarray, header: DecodedQrHeader) -> DamageMap:
    """Share of data cells in each zone of the page that were misread, rows top to bottom."""
    zones, totals = _zones(header)
    symbols = wrong[wrong < len(zones)]
    damaged = np.bincount(zones[symbols], minlength=MAP_ROWS * MAP_COLS)
    shares = np.divide(damaged, totals, out=np.zeros(MAP_ROWS * MAP_COLS), where=totals > 0)
    return tuple(tuple(round(float(value), 4) for value in row) for row in shares.reshape(MAP_ROWS, MAP_COLS))


def empty_map() -> DamageMap:
    return tuple(tuple(0.0 for _ in range(MAP_COLS)) for _ in range(MAP_ROWS))


def _zones(header: DecodedQrHeader) -> tuple[np.ndarray, np.ndarray]:
    grid = page_cell_grid(header)
    zones = (grid[:, 0] * MAP_ROWS // header.rows) * MAP_COLS + grid[:, 1] * MAP_COLS // header.cols
    return zones, np.bincount(zones, minlength=MAP_ROWS * MAP_COLS).astype(np.float64)
