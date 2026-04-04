import math
from functools import lru_cache

from reedsolo import RSCodec

GF_MAX_CODEWORD = 255


def calculate_ecc_symbols(block_size: int, redundancy: float) -> int:
    return max(2, math.ceil(block_size * redundancy))


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
