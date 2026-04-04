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
from common.page_layout import grid_dimensions, pages_needed
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


def _build_page_grid(
    symbols: list[int], page: int, cells_per_page: int, cols: int, rows: int
) -> SymbolGrid:
    start = page * cells_per_page
    page_symbols = symbols[start : start + cells_per_page]
    page_symbols = page_symbols + [-1] * (cells_per_page - len(page_symbols))
    return [page_symbols[row * cols : (row + 1) * cols] for row in range(rows)]


def payload_to_symbol_grids(
    payload: bytes,
    config: PaperClipConfig,
    total_pages: int,
) -> list[SymbolGrid]:
    symbols = bytes_to_symbols(payload, config.num_colors)
    cols, rows = grid_dimensions(config)
    cells_per_page = cols * rows
    return [
        _build_page_grid(symbols, page, cells_per_page, cols, rows)
        for page in range(total_pages)
    ]


def compute_total_pages(raw_size: int, config: PaperClipConfig) -> int:
    return pages_needed(raw_size, config)
