from calibration.sheet_pass import passed_cell, passed_symbols
from calibration.sheet_score import PatchRead
from common.config import resolve_config
from common.format_spec import DOT_DIAMETER_RATIO, MIN_CELL_MM, QR_MODULE_MM
from common.page_capacity import data_capacity_bytes

_DROP = 0.005


def safe_cell(reads: tuple[PatchRead, ...], cells: tuple[int, ...]) -> tuple[int, int]:
    """Smallest cell that still scores with the larger passing sizes."""
    best = 0.0
    chosen = (22, 5, -1)
    for cell in cells:
        if not _encodable(cell) or cell not in passed_cell(reads):
            break
        symbols = max(passed_symbols(reads, cell))
        accuracy = _accuracy(reads, cell, symbols)
        if accuracy <= 0.0 or (best and accuracy < best - _DROP):
            break
        best = max(best, accuracy)
        amount = _capacity(cell, symbols)
        if amount > chosen[2]:
            chosen = (cell, symbols, amount)
    return chosen[0], chosen[1]


def _accuracy(reads: tuple[PatchRead, ...], cell: int, symbols: int) -> float:
    matched = [read.accuracy for read in reads if _marks(read, cell, symbols)]
    return max(matched) if matched else 0.0


def _marks(read: PatchRead, cell: int, symbols: int) -> bool:
    if read.cell_px != cell or read.dot_ratio != DOT_DIAMETER_RATIO:
        return False
    if symbols == 5:
        return read.kind == "dot"
    return read.kind == "symbol" and read.symbols == symbols


def _encodable(cell: int) -> bool:
    return cell * 25.4 / 720.0 >= MIN_CELL_MM


def _capacity(cell: int, symbols: int) -> int:
    config = resolve_config(
        cell_size_px=cell, num_symbols=symbols, tag_size_mm=8.0, tag_pitch_mm=16.0,
        qr_module_mm=QR_MODULE_MM, dot_ratio=DOT_DIAMETER_RATIO, print_dpi=720,
    )
    return data_capacity_bytes(config)
