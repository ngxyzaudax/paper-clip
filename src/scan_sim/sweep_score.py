import time
from typing import NamedTuple

import numpy as np

from common.config import PaperClipConfig
from common.page_layout import valid_cells_ordered
from common.types import SymbolGrid
from serialization.decode.assemble import assemble_pages
from serialization.decode.errors import DecodeError
from serialization.decode.observe import PageObservation, observe_page


class SampleScore(NamedTuple):
    ok: bool
    symbol_errors: int
    symbol_total: int
    erasures: int | None
    seconds: float
    located: bool


def expected_symbols(grid: SymbolGrid, config: PaperClipConfig) -> list[int]:
    symbols: list[int] = []
    for row, col in valid_cells_ordered(config):
        value = int(grid[row][col])
        if value < 0:
            break
        symbols.append(value)
    return symbols


def score_scans(
    scans: list[np.ndarray],
    expected: list[list[int]],
    payload: bytes,
    model: object | None,
) -> SampleScore:
    started = time.perf_counter()
    try:
        pages = [observe_page(image, model) for image in scans]
    except DecodeError:
        total = sum(len(item) for item in expected)
        return SampleScore(False, total, total, None, time.perf_counter() - started, False)
    errors, total = _tally(pages, expected)
    erasures = sum(len(page.erasures) for page in pages)
    ok = _recovered(pages, payload)
    return SampleScore(ok, errors, total, erasures, time.perf_counter() - started, True)


def _tally(pages: list[PageObservation], expected: list[list[int]]) -> tuple[int, int]:
    errors = 0
    total = 0
    for index, symbols in enumerate(expected):
        total += len(symbols)
        if index >= len(pages):
            errors += len(symbols)
            continue
        errors += _mismatch(pages[index].symbols, symbols)
    return errors, total


def _mismatch(observed: tuple[int, ...], expected: list[int]) -> int:
    return sum(
        1
        for index, symbol in enumerate(expected)
        if index >= len(observed) or int(observed[index]) != symbol
    )


def _recovered(pages: list[PageObservation], payload: bytes) -> bool:
    try:
        raw, _name = assemble_pages(pages, None)
    except DecodeError:
        return False
    return raw == payload
