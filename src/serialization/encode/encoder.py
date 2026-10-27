from common.codec import (
    calculate_ecc_symbols,
    effective_block_size,
    interleave_blocks,
    rs_encode_block,
)
from common.compression import compress
from common.config import BLOCK_SIZE, PaperClipConfig
from common.crypto import compute_sha256
from common.encryption import DEFAULT_ENCRYPTION_PASSPHRASE, ENCRYPTION_OVERHEAD, encrypt
from common.format_spec import FLAG_USER_PASSPHRASE
from common.page_layout import (
    data_capacity_bytes,
    grid_dimensions,
    pages_needed,
    valid_cells_ordered,
)
from common.symbols import bytes_to_symbols
from common.types import SymbolGrid
from serialization.encode.frame_payload import PreparedPayload, frame_body, interleaved_length


def prepare_payload(
    raw: bytes,
    config: PaperClipConfig,
    filename: str = "",
    passphrase: str | None = None,
) -> PreparedPayload:
    compressed = compress(raw)
    flags = FLAG_USER_PASSPHRASE if passphrase else 0
    blob = encrypt(compressed, passphrase if passphrase else DEFAULT_ENCRYPTION_PASSPHRASE)
    ecc_symbols = calculate_ecc_symbols(BLOCK_SIZE, config.rs_redundancy)
    block_size = effective_block_size(ecc_symbols)
    framed, num_blocks = frame_body(blob, filename, block_size)
    payload = _encode_blocks(framed, num_blocks, ecc_symbols)
    return PreparedPayload(payload, compute_sha256(raw), len(raw), flags)


def payload_byte_length_and_hash(
    raw: bytes,
    config: PaperClipConfig,
    filename: str = "",
    passphrase: str | None = None,
) -> tuple[int, bytes]:
    del passphrase
    compressed = compress(raw)
    blob_len = len(compressed) + ENCRYPTION_OVERHEAD
    name_len = len(filename.encode("utf-8")[:255])
    ecc_symbols = calculate_ecc_symbols(BLOCK_SIZE, config.rs_redundancy)
    total = interleaved_length(blob_len, name_len, ecc_symbols)
    return total, compute_sha256(raw)


def _encode_blocks(framed: bytes, num_blocks: int, ecc_symbols: int) -> bytes:
    block_size = len(framed) // num_blocks
    blocks = [framed[index * block_size:(index + 1) * block_size] for index in range(num_blocks)]
    if len(blocks) > 0xFFFF:
        raise ValueError(f"Payload requires {len(blocks)} blocks, exceeding the 65535 maximum.")
    encoded = [rs_encode_block(block, ecc_symbols) for block in blocks]
    return interleave_blocks(encoded)


def _sparse_symbol_grid(
    symbols: list[int], cols: int, rows: int, valid_order: list[tuple[int, int]],
) -> SymbolGrid:
    grid: list[list[int]] = [[-1] * cols for _ in range(rows)]
    for index, (row, col) in enumerate(valid_order):
        if index < len(symbols):
            grid[row][col] = symbols[index]
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
        chunk = payload[page * cap:(page + 1) * cap]
        grids.append(_sparse_symbol_grid(bytes_to_symbols(chunk, config.num_symbols), cols, rows, valid_order))
    return grids


def compute_total_pages(payload_byte_length: int, config: PaperClipConfig) -> int:
    return pages_needed(payload_byte_length, config)
