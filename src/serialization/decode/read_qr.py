import numpy as np

from serialization.decode.errors import DecodeError
from serialization.decode.qr_bend import bent_qr_retry
from serialization.decode.qr_binary import binary_views
from serialization.decode.qr_centre import read_centre
from serialization.decode.qr_detect import detectors, first_header, header_from_text, rotations, views, window_header
from serialization.decode.qr_multi import QrHit, multi_hits
from serialization.encode.header_bytes import DecodedQrHeader


def read_qr_header(image: np.ndarray) -> tuple[np.ndarray, DecodedQrHeader, np.ndarray | None]:
    located = locate_qr_headers(image)
    if located is None:
        raise DecodeError("QR header not found")
    rotated, hits = located
    points = hits[0].points if len(hits[0].points) == 4 else None
    return rotated, hits[0].header, points


def locate_qr_headers(image: np.ndarray) -> tuple[np.ndarray, tuple[QrHit, ...]] | None:
    hits = multi_hits(image)
    if hits:
        return image, hits
    found = _single(image)
    if found is not None:
        return found
    rescued = bent_qr_retry(image, detectors(), header_from_text)
    if rescued is not None:
        return image, (_hit(rescued[0], rescued[1]),)
    for rotated in rotations(image):
        hits = multi_hits(rotated)
        if hits:
            return rotated, hits
        found = _first(rotated)
        if found is not None:
            return found
    return None


def _single(image: np.ndarray) -> tuple[np.ndarray, tuple[QrHit, ...]] | None:
    found = detectors()
    hit = _centre(image, found) or window_header(image, found) or first_header(image, (image,), found)
    if hit is None:
        return None
    rotated, header, points = hit
    return rotated, (_hit(header, points),)


def _first(rotated: np.ndarray) -> tuple[np.ndarray, tuple[QrHit, ...]] | None:
    hit = first_header(rotated, views(rotated), detectors())
    if hit is None:
        return None
    image, header, points = hit
    return image, (_hit(header, points),)


def _centre(
    image: np.ndarray, found: tuple[object, ...],
) -> tuple[np.ndarray, DecodedQrHeader, np.ndarray | None] | None:
    def decode(view: np.ndarray) -> tuple[DecodedQrHeader, np.ndarray | None] | None:
        hit = first_header(view, views(view) + binary_views(view), found)
        if hit is None:
            return None
        _rotated, header, points = hit
        return header, points

    return read_centre(image, decode)


def _hit(header: DecodedQrHeader, points: np.ndarray | None) -> QrHit:
    quad = np.zeros((0, 2), np.float32) if points is None else np.asarray(points, np.float32).reshape(-1, 2)
    return QrHit(header, quad)
