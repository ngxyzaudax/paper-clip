import logging

from common.codec import (
    calculate_ecc_symbols,
    deinterleave_blocks,
    effective_block_size,
    rs_decode_block,
)
from common.compression import decompress
from common.config import (
    BLOCK_SIZE,
    PAYLOAD_HEADER_REDUNDANCY,
    PAYLOAD_HEADER_STRUCT,
    PaperClipConfig,
)
from common.crypto import verify_sha256
from common.symbols import chunk_params, symbol_count, symbols_to_bytes as symbols_to_raw_bytes
from common.types import SymbolGrid

logger = logging.getLogger(__name__)


def _majority_vote_payload_header(raw: bytes) -> bytes:
    hdr_size = PAYLOAD_HEADER_STRUCT.size
    copies = [
        raw[i * hdr_size : (i + 1) * hdr_size]
        for i in range(PAYLOAD_HEADER_REDUNDANCY)
        if (i + 1) * hdr_size <= len(raw)
    ]
    if not copies:
        return raw[:hdr_size]
    result = bytearray(hdr_size)
    for i in range(hdr_size):
        votes: dict[int, int] = {}
        for copy in copies:
            if i < len(copy):
                votes[copy[i]] = votes.get(copy[i], 0) + 1
        result[i] = max(votes, key=lambda v: votes[v])
    return bytes(result)


def _decode_payload(
    raw_payload: bytes,
    ecc_symbols: int,
    bs: int,
    encoded_block_size: int,
    encrypted: bool = False,
    passphrase: str | None = None,
) -> tuple[bytes, str]:
    hdr_size = PAYLOAD_HEADER_STRUCT.size
    redundant_size = hdr_size * PAYLOAD_HEADER_REDUNDANCY
    payload_header = _majority_vote_payload_header(raw_payload[:redundant_size])
    compressed_size, num_blocks, filename_len = PAYLOAD_HEADER_STRUCT.unpack(payload_header)
    if compressed_size <= 0 or compressed_size > len(raw_payload):
        raise ValueError("Invalid compressed_size")
    if num_blocks <= 0 or num_blocks > 100000:
        raise ValueError("Invalid num_blocks")
    filename = raw_payload[redundant_size:redundant_size + filename_len].decode("utf-8", errors="replace")
    interleaved = raw_payload[redundant_size + filename_len:]
    blocks = deinterleave_blocks(interleaved, num_blocks, encoded_block_size)
    decoded_blocks: list[bytes] = []
    failed_indices: list[int] = []
    for idx, block in enumerate(blocks):
        try:
            decoded_blocks.append(rs_decode_block(block, ecc_symbols))
        except Exception:
            failed_indices.append(idx)
            logger.warning("RS decode failed on block %d/%d", idx + 1, len(blocks))
    if failed_indices:
        raise ValueError(
            f"Reed-Solomon decoding failed on {len(failed_indices)}/{len(blocks)} "
            f"blocks (indices: {failed_indices[:10]}). Data is unrecoverable."
        )
    all_decoded = b"".join(decoded_blocks)
    compressed_blob = all_decoded[:compressed_size]
    if encrypted:
        compressed_blob = _handle_decryption(compressed_blob, passphrase)
    return decompress(compressed_blob), filename


def _handle_decryption(blob: bytes, passphrase: str | None) -> bytes:
    from common.keystore import try_stored_passwords
    if passphrase:
        from common.encryption import decrypt
        return decrypt(blob, passphrase)
    result = try_stored_passwords(blob)
    if result is not None:
        return result[0]
    raise ValueError("Encrypted data: no valid password found. Provide --password or save one.")


def grid_to_raw_bytes(grid: SymbolGrid, config: PaperClipConfig) -> bytes:
    all_symbols: list[int] = []
    for row in grid:
        all_symbols.extend(row)
    n = symbol_count(config.num_colors)
    k, m = chunk_params(n)
    total_payload_bytes = (len(all_symbols) // m) * k
    return symbols_to_raw_bytes(all_symbols, config.num_colors, total_payload_bytes)


def symbols_to_bytes(
    grids: list[SymbolGrid],
    config: PaperClipConfig,
    expected_data_length: int,
    sha256_hash: bytes,
    encrypted: bool = False,
    passphrase: str | None = None,
) -> tuple[bytes, str]:
    all_symbols: list[int] = []
    for grid in grids:
        for row in grid:
            all_symbols.extend(row)
    n = symbol_count(config.num_colors)
    k, m = chunk_params(n)
    ecc_symbols = calculate_ecc_symbols(BLOCK_SIZE, config.rs_redundancy)
    bs = effective_block_size(ecc_symbols)
    encoded_block_size = bs + ecc_symbols
    total_payload_bytes = (len(all_symbols) // m) * k
    raw_payload = symbols_to_raw_bytes(
        all_symbols, config.num_colors, total_payload_bytes
    )
    decompressed, filename = _decode_payload(
        raw_payload, ecc_symbols, bs, encoded_block_size, encrypted, passphrase,
    )
    result = decompressed[:expected_data_length]
    if not verify_sha256(result, sha256_hash):
        raise ValueError("SHA-256 integrity check failed")
    return result, filename


def raw_payload_to_bytes(
    raw_payload: bytes,
    config: PaperClipConfig,
    expected_data_length: int,
    sha256_hash: bytes,
    encrypted: bool = False,
    passphrase: str | None = None,
) -> tuple[bytes, str]:
    ecc_symbols = calculate_ecc_symbols(BLOCK_SIZE, config.rs_redundancy)
    bs = effective_block_size(ecc_symbols)
    encoded_block_size = bs + ecc_symbols
    decompressed, filename = _decode_payload(
        raw_payload, ecc_symbols, bs, encoded_block_size, encrypted, passphrase,
    )
    result = decompressed[:expected_data_length]
    if not verify_sha256(result, sha256_hash):
        raise ValueError("SHA-256 integrity check failed")
    return result, filename
