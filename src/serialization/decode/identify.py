from typing import NamedTuple

import numpy as np

from common.format_spec import FLAG_DUPLEX, FLAG_USER_PASSPHRASE
from serialization.decode.qr_detect import rotations
from serialization.decode.qr_multi import QrHit, multi_hits
from serialization.decode.read_qr import locate_qr_headers
from serialization.encode.header_bytes import DecodedQrHeader

_ANGLES = (0, 90, 180, 270)


class ScanIdentity(NamedTuple):
    page_index: int
    total_pages: int
    data_pages: int
    sha256: str
    passphrase_required: bool
    duplex: bool
    page_indices: tuple[int, ...]
    rotation: int
    header: DecodedQrHeader


def identify_scan(image: np.ndarray) -> ScanIdentity | None:
    for angle, turned in zip(_ANGLES, rotations(image), strict=True):
        hits = multi_hits(turned)
        if hits:
            return _identity(hits, (angle + _edge_rotation(hits[0].points)) % 360)
    located = locate_qr_headers(image)
    if located is None:
        return None
    _rotated, hits = located
    return _identity(hits, 0)


def _edge_rotation(points: np.ndarray) -> int:
    delta = points[1] - points[0]
    degrees = float(np.degrees(np.arctan2(float(delta[1]), float(delta[0]))))
    return int(round(degrees / 90.0) * 90) % 360


def _identity(hits: tuple[QrHit, ...], rotation: int) -> ScanIdentity:
    header = hits[0].header
    indices = tuple(sorted({hit.header.page_index for hit in hits}))
    return ScanIdentity(
        header.page_index,
        header.total_pages,
        header.data_pages,
        header.original_sha256.hex(),
        bool(header.flags & FLAG_USER_PASSPHRASE),
        bool(header.flags & FLAG_DUPLEX),
        indices,
        rotation,
        header,
    )
