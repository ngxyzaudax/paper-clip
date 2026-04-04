from common.codec import (
    calculate_ecc_symbols,
    effective_block_size,
    interleave_blocks,
    rs_encode_block,
)
from common.compression import compress
from common.config import (
    BLOCK_SIZE,
    PAYLOAD_HEADER_REDUNDANCY,
    PAYLOAD_HEADER_STRUCT,
    PaperClipConfig,
)
from common.crypto import compute_sha256
from common.page_layout import (
    data_capacity_bytes,
    grid_dimensions,
    pages_needed,
    valid_cells_ordered,
)
from common.symbols import bytes_to_symbols
from common.types import SymbolGrid


def prepare_payload(
    raw: bytes,
    config: PaperClipConfig,
    filename: str = "",
    passphrase: str | None = None,
) -> tuple[bytes, bytes]:
    sha256_hash = compute_sha256(raw)
    compressed = compress(raw)
    if passphrase:
        from common.encryption import encrypt
        compressed = encrypt(compressed, passphrase)
    ecc_symbols = calculate_ecc_symbols(BLOCK_SIZE, config.rs_redundancy)
    bs = effective_block_size(ecc_symbols)
    blocks = _split_into_blocks(compressed, bs)
    num_blocks = len(blocks)
    if num_blocks > 0xFFFF:
        raise ValueError(
            f"Payload requires {num_blocks} blocks, exceeding the 65535 maximum. "
            "Reduce input size or increase block capacity."
        )
    encoded_blocks = [rs_encode_block(block, ecc_symbols) for block in blocks]
    interleaved = interleave_blocks(encoded_blocks)
    fname_bytes = filename.encode("utf-8")[:255]
    payload_header = PAYLOAD_HEADER_STRUCT.pack(len(compressed), num_blocks, len(fname_bytes))
    redundant_header = payload_header * PAYLOAD_HEADER_REDUNDANCY
    return redundant_header + fname_bytes + interleaved, sha256_hash


def _split_into_blocks(data: bytes, block_size: int) -> list[bytes]:
    return [
        data[i : i + block_size].ljust(block_size, b"\x00")
        for i in range(0, len(data), block_size)
    ]


def _sparse_symbol_grid(
    symbols: list[int], cols: int, rows: int, valid_order: list[tuple[int, int]],
) -> SymbolGrid:
    grid: list[list[int]] = [[-1] * cols for _ in range(rows)]
    for i, (row, col) in enumerate(valid_order):
        if i < len(symbols):
            grid[row][col] = symbols[i]
    return grid


def payload_to_symbol_grids(
    payload: bytes,
    config: PaperClipConfig,
    total_pages: int,
) -> list[SymbolGrid]:
    cols, rows = grid_dimensions(config)
    valid_order = valid_cells_ordered(config)
    cap = data_capacity_bytes(config)
    grids: list[SymbolGrid] = []
    for page in range(total_pages):
        chunk = payload[page * cap : (page + 1) * cap]
        syms = bytes_to_symbols(chunk, config.num_colors)
        grids.append(_sparse_symbol_grid(syms, cols, rows, valid_order))
    return grids


def compute_total_pages(raw_size: int, config: PaperClipConfig) -> int:
    return pages_needed(raw_size, config)
