from typing import NamedTuple

import cv2
import numpy as np

from serialization.decode.qr_detect import detectors, header_from_text, views
from serialization.encode.header_bytes import DecodedQrHeader

_SAME_CODE_PX = 40.0


class QrHit(NamedTuple):
    header: DecodedQrHeader
    points: np.ndarray


def multi_hits(image: np.ndarray) -> tuple[QrHit, ...]:
    found: list[QrHit] = []
    for view in views(image):
        found.extend(_hits(view))
        if found:
            return _dedupe(found)
    return ()


def _hits(image: np.ndarray) -> list[QrHit]:
    found: list[QrHit] = []
    for detector in detectors():
        for text, points in _multi(detector, image):
            header = header_from_text(text)
            if header is not None and len(points) == 4:
                found.append(QrHit(header, points))
    return found


def _multi(detector: object, image: np.ndarray) -> list[tuple[str, np.ndarray]]:
    method = getattr(detector, "detectAndDecodeMulti", None)
    if method is None:
        return []
    try:
        result = method(cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    except Exception:
        return []
    if not result or not result[0] or result[2] is None:
        return []
    found: list[tuple[str, np.ndarray]] = []
    for text, quad in zip(result[1] or (), result[2]):
        if text:
            found.append((str(text), np.asarray(quad, np.float32).reshape(-1, 2)))
    return found


def _dedupe(hits: list[QrHit]) -> tuple[QrHit, ...]:
    kept: list[QrHit] = []
    for hit in hits:
        centre = hit.points.mean(axis=0)
        if any(float(np.linalg.norm(centre - other.points.mean(axis=0))) < _SAME_CODE_PX for other in kept):
            continue
        kept.append(hit)
    return tuple(kept)
