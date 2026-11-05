from itertools import accumulate

import numpy as np

from common.symbols import bytes_to_symbols
from serialization.decode.assemble_slots import Assembly
from serialization.decode.erasures import ERASURE_CONFIDENCE
from serialization.decode.observe import PageObservation

NO_CELLS = np.zeros(0, np.int64)


def observed_wrong(assembly: Assembly) -> tuple[np.ndarray, ...]:
    """For each scanned page, the indexes of the cells whose colour was misread, found against the corrected data."""
    slices = page_fixed_slices(assembly.repair.fixed, assembly.page_sizes)
    return tuple(
        wrong_symbols(page, slices[page.header.page_index]) if page.header.page_index < len(slices) else NO_CELLS
        for page in assembly.observed
    )


def page_fixed_slices(fixed: bytes, page_sizes: tuple[int, ...]) -> list[bytes]:
    ends = list(accumulate(page_sizes))
    return [fixed[end - size:end] for end, size in zip(ends, page_sizes)]


def wrong_symbols(page: PageObservation, fixed_slice: bytes) -> np.ndarray:
    if not fixed_slice:
        return NO_CELLS
    corrected = fixed_slice + page.data[len(fixed_slice):]
    seen = np.asarray(page.symbols, np.int64)
    right = np.asarray(bytes_to_symbols(corrected, page.header.num_symbols)[:len(seen)], np.int64)
    return np.flatnonzero(seen[:len(right)] != right)


def unsure_symbols(page: PageObservation) -> np.ndarray:
    return np.flatnonzero(np.asarray(page.confidence, np.float32) < ERASURE_CONFIDENCE)
