from common.codec import rs_decode_block
from common.format_spec import HEADER_GRID_COPIES, HEADER_GRID_ECC
from common.header_grid import header_codeword_length
from serialization.encode.header_bytes import DecodedQrHeader, decode_header_bytes


def header_from_grid_bytes(blob: bytes, erasures: list[int]) -> DecodedQrHeader | None:
    size = header_codeword_length()
    if len(blob) < size * HEADER_GRID_COPIES:
        return None
    copies = [blob[index * size:(index + 1) * size] for index in range(HEADER_GRID_COPIES)]
    groups = [[pos - index * size for pos in erasures if index * size <= pos < (index + 1) * size] for index in range(HEADER_GRID_COPIES)]
    for copy, erased in zip(copies, groups):
        found = _repair(copy, erased)
        if found is not None:
            return found
    merged, erased = _merge(copies)
    return _repair(merged, erased)


def _repair(codeword: bytes, erasures: list[int]) -> DecodedQrHeader | None:
    size = header_codeword_length()
    if len(codeword) != size:
        return None
    cleaned = sorted({pos for pos in erasures if 0 <= pos < size})
    if len(cleaned) > HEADER_GRID_ECC:
        return None
    try:
        return decode_header_bytes(rs_decode_block(codeword, HEADER_GRID_ECC, cleaned))
    except Exception:
        return None


def _merge(copies: list[bytes]) -> tuple[bytes, list[int]]:
    length = len(copies[0])
    merged = bytearray(length)
    erased: list[int] = []
    for index in range(length):
        values = {copy[index] for copy in copies}
        if len(values) == 1:
            merged[index] = values.pop()
        else:
            erased.append(index)
    return bytes(merged), erased
