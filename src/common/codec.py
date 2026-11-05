from functools import lru_cache

from reedsolo import RSCodec

GF_MAX_CODEWORD = 255


def effective_block_size(ecc_symbols: int) -> int:
    return min(200, GF_MAX_CODEWORD - ecc_symbols)


@lru_cache(maxsize=8)
def _get_codec(ecc_symbols: int) -> RSCodec:
    return RSCodec(ecc_symbols)


def rs_encode_block(data: bytes, ecc_symbols: int) -> bytes:
    return bytes(_get_codec(ecc_symbols).encode(data))


def interleave_blocks(blocks: list[bytes]) -> bytes:
    if not blocks:
        return b""
    max_len = max(len(b) for b in blocks)
    result = bytearray(sum(min(len(b), max_len) for b in blocks))
    idx = 0
    for col in range(max_len):
        for block in blocks:
            if col < len(block):
                result[idx] = block[col]
                idx += 1
    return bytes(result)


def deinterleave_blocks(data: bytes, num_blocks: int, codeword_len: int) -> list[bytes]:
    if num_blocks <= 0 or codeword_len <= 0:
        raise ValueError("invalid interleave shape")
    needed = num_blocks * codeword_len
    if len(data) < needed:
        raise ValueError("interleaved payload is short")
    blocks = [bytearray(codeword_len) for _ in range(num_blocks)]
    index = 0
    for col in range(codeword_len):
        for block in blocks:
            block[col] = data[index]
            index += 1
    return [bytes(block) for block in blocks]


def rs_decode_block(
    data: bytes, ecc_symbols: int, erase_pos: list[int] | None = None,
) -> bytes:
    return rs_repair_block(data, ecc_symbols, erase_pos)[0]


def rs_repair_block(
    data: bytes, ecc_symbols: int, erase_pos: list[int] | None = None,
) -> tuple[bytes, tuple[int, ...], bytes]:
    """Decoded message, positions found as errors beyond the given erasures, and the corrected codeword."""
    codec = _get_codec(ecc_symbols)
    erased = list(erase_pos or ())
    decoded, codeword, errata = codec.decode(bytearray(data), erase_pos=erased or None)
    known = set(erased)
    errors = tuple(sorted(int(pos) for pos in errata if int(pos) not in known))
    return bytes(decoded), errors, bytes(codeword)


def rs_encoded_stream_data_vs_parity(
    total_encoded_bytes: int,
    ecc_symbols: int,
) -> tuple[int, int]:
    if total_encoded_bytes <= 0:
        return 0, 0
    ecc = ecc_symbols
    bs = effective_block_size(ecc)
    denom = bs + ecc
    if denom <= 0:
        return 0, total_encoded_bytes
    data_bytes = (total_encoded_bytes * bs) // denom
    parity_bytes = total_encoded_bytes - data_bytes
    return data_bytes, parity_bytes
