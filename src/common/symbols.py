import math
from functools import lru_cache


def bits_per_cell(num_symbols: int) -> float:
    return math.log2(num_symbols)


@lru_cache(maxsize=32)
def chunk_params(n: int) -> tuple[int, int]:
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


def bytes_to_symbols(data: bytes, num_symbols: int) -> list[int]:
    n = num_symbols
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


def symbols_to_bytes(symbols: list[int], num_symbols: int, expected_byte_count: int) -> bytes:
    n = num_symbols
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
