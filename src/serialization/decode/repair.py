from collections.abc import Callable
from typing import NamedTuple

from common.codec import deinterleave_blocks, interleave_blocks, rs_repair_block
from serialization.decode.errors import DecodeError

BlockResult = tuple[bytes, tuple[int, ...], bytes]


class BlockRepair(NamedTuple):
    errors: int
    erasures: int


class StreamRepair(NamedTuple):
    ecc_sym: int
    blocks: tuple[BlockRepair, ...]
    repaired: tuple[int, ...]
    damaged: tuple[int, ...] = ()
    fixed: bytes = b""


def repair_blocks(
    payload: bytes, num_blocks: int, codeword: int, ecc_symbols: int, erasures: list[int],
) -> tuple[bytes, StreamRepair]:
    """Decode every interleaved block and report how much of each block's parity the repair used."""
    grouped = _erasures_by_block(erasures, num_blocks, codeword)
    blocks = deinterleave_blocks(payload, num_blocks, codeword)
    results = [
        _repair(block, ecc_symbols, grouped.get(index, []), len(erasures))
        for index, block in enumerate(blocks)
    ]
    framed = b"".join(result[0] for result in results)
    repairs = tuple(
        BlockRepair(len(result[1]), len(grouped.get(index, []))) for index, result in enumerate(results)
    )
    repaired = _positions(results, grouped, num_blocks, lambda result, erased: (*result[1], *erased))
    fixed = interleave_blocks([result[2] for result in results])
    damaged = tuple(index for index, (seen, right) in enumerate(zip(payload, fixed)) if seen != right)
    return framed, StreamRepair(ecc_symbols, repairs, repaired, damaged, fixed)


def _erasures_by_block(erasures: list[int], num_blocks: int, codeword: int) -> dict[int, list[int]]:
    grouped: dict[int, set[int]] = {}
    for position in erasures:
        column = position // num_blocks
        if 0 <= column < codeword:
            grouped.setdefault(position % num_blocks, set()).add(column)
    return {index: sorted(columns) for index, columns in grouped.items()}


def _repair(block: bytes, ecc_symbols: int, erase: list[int], total_erasures: int) -> BlockResult:
    try:
        return rs_repair_block(block, ecc_symbols, erase or None)
    except Exception as exc:
        raise DecodeError(f"Reed-Solomon decode failed with {total_erasures} erasures: {exc}") from exc


def _positions(
    results: list[BlockResult],
    grouped: dict[int, list[int]],
    num_blocks: int,
    columns_of: Callable[[BlockResult, list[int]], tuple[int, ...]],
) -> tuple[int, ...]:
    positions = {
        column * num_blocks + index
        for index, result in enumerate(results)
        for column in columns_of(result, grouped.get(index, []))
    }
    return tuple(sorted(positions))
