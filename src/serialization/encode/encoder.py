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
from common.encryption import DEFAULT_ENCRYPTION_PASSPHRASE, ENCRYPTION_OVERHEAD, encrypt
from common.page_layout import (
    data_capacity_bytes,
    grid_dimensions,
    pages_needed,
    valid_cells_ordered,
)
from common.symbols import bytes_to_symbols
from common.types import SymbolGrid


def _effective_passphrase(passphrase: str | None) -> str:
    return passphrase if passphrase else DEFAULT_ENCRYPTION_PASSPHRASE


def _prepare_payload_bytes(
    raw: bytes,
    config: PaperClipConfig,
    filename: str,
    passphrase: str | None,
) -> bytes:
    compressed = compress(raw)
    blob = encrypt(compressed, _effective_passphrase(passphrase))
    ecc_symbols = calculate_ecc_symbols(BLOCK_SIZE, config.rs_redundancy)
    bs = effective_block_size(ecc_symbols)
    blocks = _split_into_blocks(blob, bs)
    num_blocks = len(blocks)
    if num_blocks > 0xFFFF:
        raise ValueError(
            f"Payload requires {num_blocks} blocks, exceeding the 65535 maximum. "
            "Reduce input size or increase block capacity."
        )
    encoded_blocks = [rs_encode_block(block, ecc_symbols) for block in blocks]
    interleaved = interleave_blocks(encoded_blocks)
    fname_bytes = filename.encode("utf-8")[:255]
    payload_header = PAYLOAD_HEADER_STRUCT.pack(len(blob), num_blocks, len(fname_bytes))
    redundant_header = payload_header * PAYLOAD_HEADER_REDUNDANCY
    return redundant_header + fname_bytes + interleaved


def payload_byte_length_and_hash(
    raw: bytes,
    config: PaperClipConfig,
    filename: str = "",
    passphrase: str | None = None,
) -> tuple[int, bytes]:
    compressed = compress(raw)
    blob_len = len(compressed) + ENCRYPTION_OVERHEAD
    blob = bytes(blob_len)
    ecc_symbols = calculate_ecc_symbols(BLOCK_SIZE, config.rs_redundancy)
    bs = effective_block_size(ecc_symbols)
    blocks = _split_into_blocks(blob, bs)
    num_blocks = len(blocks)
    if num_blocks > 0xFFFF:
        raise ValueError(
            f"Payload requires {num_blocks} blocks, exceeding the 65535 maximum. "
            "Reduce input size or increase block capacity."
        )
    if not blocks:
        interleaved_len = 0
    else:
        enc0 = rs_encode_block(blocks[0], ecc_symbols)
        interleaved_len = num_blocks * len(enc0)
    fname_bytes = filename.encode("utf-8")[:255]
    payload_header = PAYLOAD_HEADER_STRUCT.pack(blob_len, num_blocks, len(fname_bytes))
    redundant_header = payload_header * PAYLOAD_HEADER_REDUNDANCY
    total_len = len(redundant_header) + len(fname_bytes) + interleaved_len
    return total_len, b""


def prepare_payload(
    raw: bytes,
    config: PaperClipConfig,
    filename: str = "",
    passphrase: str | None = None,
) -> tuple[bytes, bytes]:
    payload = _prepare_payload_bytes(raw, config, filename, passphrase)
    return payload, compute_sha256(payload)


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
        syms = bytes_to_symbols(chunk, config.num_symbols)
        grids.append(_sparse_symbol_grid(syms, cols, rows, valid_order))
    return grids


def compute_total_pages(payload_byte_length: int, config: PaperClipConfig) -> int:
    return pages_needed(payload_byte_length, config)
