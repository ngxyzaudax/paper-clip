from typing import NamedTuple

from common.format_spec import CALIBRATION_REPEATS
from common.geometry_qr import qr_side_px
from common.types import Region


class CentreBlock(NamedTuple):
    qr: Region
    calibration: Region
    block: Region


def centre_block(
    page_w: int,
    page_h: int,
    origin_x: int,
    origin_y: int,
    cols: int,
    rows: int,
    cell: int,
    dpi: int,
    num_symbols: int,
) -> CentreBlock:
    side = qr_side_px(dpi)
    qr_cells = -(-side // cell)
    block_cols = max(qr_cells, num_symbols + 2)
    block_rows = qr_cells + CALIBRATION_REPEATS + 1
    if block_cols > cols or block_rows > rows:
        raise ValueError("page is too small for the centred QR header and calibration strip")
    col0 = _centred_start((page_w / 2.0 - origin_x) / cell, block_cols, cols, block_cols)
    row0 = _centred_start((page_h / 2.0 - origin_y) / cell, qr_cells, rows, block_rows)
    left = col0 * cell
    top = row0 * cell
    qr = Region(
        left + (block_cols * cell - side) // 2,
        top + (qr_cells * cell - side) // 2,
        side,
        side,
    )
    calibration = Region(
        left + ((block_cols - num_symbols) // 2) * cell,
        top + qr_cells * cell,
        num_symbols * cell,
        CALIBRATION_REPEATS * cell,
    )
    block = Region(left, top, block_cols * cell, block_rows * cell)
    return CentreBlock(qr, calibration, block)


def _centred_start(centre_cells: float, span: int, limit: int, extent: int) -> int:
    start = int(round(centre_cells - span / 2.0))
    return max(0, min(limit - extent, start))
