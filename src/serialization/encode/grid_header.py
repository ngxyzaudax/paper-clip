from common.codec import rs_encode_block
from common.config import PaperClipConfig
from common.format_spec import HEADER_GRID_COPIES, HEADER_GRID_ECC
from common.header_cells import split_cells
from common.header_grid import header_codeword_length
from common.symbols import bytes_to_symbols
from common.types import SymbolGrid


def grid_header_payload(header: bytes) -> bytes:
    coded = rs_encode_block(header, HEADER_GRID_ECC)
    if len(coded) != header_codeword_length():
        raise ValueError("header codeword has an unexpected length")
    return coded * HEADER_GRID_COPIES


def place_grid_header(grid: SymbolGrid, header: bytes, config: PaperClipConfig) -> SymbolGrid:
    symbols = bytes_to_symbols(grid_header_payload(header), config.num_symbols)
    cells, _data = split_cells(config)
    if len(symbols) != len(cells):
        raise ValueError(f"in-grid header needs {len(cells)} cells, got {len(symbols)} symbols")
    placed = [row.copy() for row in grid]
    for (row, col), symbol in zip(cells, symbols):
        placed[row][col] = symbol
    return placed
