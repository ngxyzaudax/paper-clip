from typing import NamedTuple

import numpy as np

from serialization.encode.header_bytes import DecodedQrHeader


class PageObservation(NamedTuple):
    header: DecodedQrHeader
    data: bytes
    erasures: tuple[int, ...]
    symbols: tuple[int, ...]
    confidence: tuple[float, ...]
    preview: np.ndarray
    preview_scale: float
    cell_shift: tuple[int, int]
    header_source: str = "qr"
    qr_copies_read: int = 0
    qr_slots_read: tuple[bool, ...] = ()
    inferred_from: int = -1
