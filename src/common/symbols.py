import math
from functools import lru_cache


def symbol_count(num_colors: int) -> int:
    return num_colors + 1


def bits_per_cell(num_colors: int) -> float:
    return math.log2(symbol_count(num_colors))


@lru_cache(maxsize=32)
def chunk_params(n: int) -> tuple[int, int]:
    """Find optimal (chunk_bytes, chunk_symbols) for base-n encoding.

    Returns the pair where 256^chunk_bytes <= n^chunk_symbols and the bit
    efficiency (chunk_bytes * 8) / (chunk_symbols * log2(n)) is maximized.
    """
    best_eff = 0.0
    log2_n = math.log2(n)
    best = (1, math.ceil(8 / log2_n))
    for k in range(1, 8):
        m = math.ceil(k * 8 / log2_n)
        if n ** m < 256 ** k:
            m += 1
        eff = (k * 8) / (m * log2_n)
        if eff > best_eff:
            best_eff = eff
            best = (k, m)
    return best


def symbol_to_color_index(symbol: int) -> int:
    return max(0, symbol - 1)


def color_index_to_symbol(color_index: int) -> int:
    return color_index + 1


def bytes_to_symbols(data: bytes, num_colors: int) -> list[int]:
    n = symbol_count(num_colors)
    k, m = chunk_params(n)
    symbols: list[int] = []
    for i in range(0, len(data), k):
        chunk = data[i:i + k]
        if len(chunk) < k:
            chunk = chunk + b"\x00" * (k - len(chunk))
        value = int.from_bytes(chunk, "big")
        chunk_syms: list[int] = [0] * m
        for j in range(m - 1, -1, -1):
            chunk_syms[j] = value % n
            value //= n
        symbols.extend(chunk_syms)
    return symbols


def symbols_to_bytes(symbols: list[int], num_colors: int, expected_byte_count: int) -> bytes:
    n = symbol_count(num_colors)
    k, m = chunk_params(n)
    max_value = 256 ** k
    result = bytearray()
    for i in range(0, len(symbols), m):
        chunk = symbols[i:i + m]
        value = 0
        for sym in chunk:
            if sym < 0 or sym >= n:
                raise ValueError(
                    f"Symbol value {sym} out of range [0, {n - 1}] at position {i}"
                )
            value = value * n + sym
        result.extend((value % max_value).to_bytes(k, "big"))
    return bytes(result[:expected_byte_count])
