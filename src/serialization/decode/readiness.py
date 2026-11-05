from collections.abc import Iterable
from typing import NamedTuple


class Readiness(NamedTuple):
    state: str
    missing: tuple[int, ...]
    data_pages: int
    total_pages: int
    parity_pages: int


def document_readiness(data_pages: int, total_pages: int, seen: Iterable[int]) -> Readiness:
    found = {index for index in seen if 0 <= index < total_pages}
    missing = tuple(index for index in range(total_pages) if index not in found)
    parity_pages = total_pages - data_pages
    data_missing = any(index < data_pages for index in missing)
    if not data_missing:
        state = "ready"
    elif parity_pages > 0 and len(missing) <= parity_pages:
        state = "parity"
    else:
        state = "missing"
    return Readiness(state, missing, data_pages, total_pages, parity_pages)
