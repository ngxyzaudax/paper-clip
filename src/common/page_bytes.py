import math
from typing import NamedTuple

from common.symbols import chunk_params


class PageBytePlan(NamedTuple):
    slice_len: tuple[int, ...]
    read_len: tuple[int, ...]
    parity_len: int


def page_byte_plan(
    payload_length: int, capacity: int, data_pages: int, num_symbols: int,
) -> PageBytePlan:
    k, _ = chunk_params(num_symbols)
    slices: list[int] = []
    reads: list[int] = []
    for index in range(data_pages):
        start = index * capacity
        size = max(0, min(capacity, payload_length - start))
        slices.append(size)
        reads.append(int(math.ceil(size / k)) * k if size else 0)
    parity_len = max(reads) if reads else 0
    return PageBytePlan(tuple(slices), tuple(reads), parity_len)


def symbol_count_for_bytes(nbytes: int, num_symbols: int) -> int:
    if nbytes <= 0:
        return 0
    k, m = chunk_params(num_symbols)
    return int(math.ceil(nbytes / k)) * m
