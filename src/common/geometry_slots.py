from common.format_spec import CALIBRATION_REPEATS, HEADER_COPIES
from common.geometry_qr import qr_side_px
from common.geometry_types import HeaderSlot
from common.types import Region

ANCHORS = ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75))


def header_slots(
    cols: int,
    rows: int,
    cell: int,
    dpi: int,
    num_symbols: int,
    qr_module_mm: float,
) -> tuple[HeaderSlot, ...]:
    side, qr_cells, block_cols, block_rows = _span(cell, dpi, num_symbols, qr_module_mm)
    if block_cols > cols or block_rows > rows:
        raise ValueError("page is too small for four header copies")
    slots = tuple(
        _anchored(fx, fy, cols, rows, cell, side, qr_cells, block_cols, block_rows, num_symbols)
        for fx, fy in ANCHORS
    )
    if len(slots) != HEADER_COPIES or _crowded(slots):
        raise ValueError("page is too small for four separated header copies")
    return slots


def _span(cell: int, dpi: int, num_symbols: int, qr_module_mm: float) -> tuple[int, int, int, int]:
    side = qr_side_px(dpi, qr_module_mm)
    qr_cells = -(-side // cell)
    return side, qr_cells, max(qr_cells, num_symbols + 2), qr_cells + CALIBRATION_REPEATS + 1


def _anchored(
    fx: float,
    fy: float,
    cols: int,
    rows: int,
    cell: int,
    side: int,
    qr_cells: int,
    block_cols: int,
    block_rows: int,
    num_symbols: int,
) -> HeaderSlot:
    col0 = _fit(int(round(fx * cols - block_cols / 2.0)), cols, block_cols)
    row0 = _fit(int(round(fy * rows - block_rows / 2.0)), rows, block_rows)
    return _slot(col0 * cell, row0 * cell, cell, side, qr_cells, block_cols, block_rows, num_symbols)


def _slot(
    left: int,
    top: int,
    cell: int,
    side: int,
    qr_cells: int,
    block_cols: int,
    block_rows: int,
    num_symbols: int,
) -> HeaderSlot:
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
    return HeaderSlot(qr, calibration, Region(left, top, block_cols * cell, block_rows * cell))


def _fit(start: int, limit: int, extent: int) -> int:
    return max(0, min(limit - extent, start))


def _crowded(slots: tuple[HeaderSlot, ...]) -> bool:
    blocks = [slot.block for slot in slots]
    return any(_overlap(blocks[index], blocks[other]) for index in range(len(blocks)) for other in range(index + 1, len(blocks)))


def _overlap(a: Region, b: Region) -> bool:
    return not (a.x + a.width <= b.x or b.x + b.width <= a.x or a.y + a.height <= b.y or b.y + b.height <= a.y)
