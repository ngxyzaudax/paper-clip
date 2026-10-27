import base64
import binascii
import struct

import cv2
import numpy as np

from serialization.decode.errors import DecodeError
from serialization.decode.qr_bend import bent_qr_retry
from serialization.encode.qr_header import DecodedQrHeader, decode_header_bytes


def read_qr_header(image: np.ndarray) -> tuple[np.ndarray, DecodedQrHeader, np.ndarray | None]:
    detectors = _detectors()
    found = _first_header(image, (image,), detectors)
    if found is not None:
        return found
    rescued = bent_qr_retry(image, detectors, _header_from_text)
    if rescued is not None:
        header, points = rescued
        return image, header, points
    for rotated in _rotations(image):
        found = _first_header(rotated, _views(rotated), detectors)
        if found is not None:
            return found
    raise DecodeError("QR header not found")


def _first_header(
    rotated: np.ndarray, views: tuple[np.ndarray, ...], detectors: tuple[object, ...],
) -> tuple[np.ndarray, DecodedQrHeader, np.ndarray | None] | None:
    for view in views:
        for detector in detectors:
            text, points = _detect(detector, view)
            header = _header_from_text(text)
            if header is not None:
                return rotated, header, points
    return None


def _rotations(image: np.ndarray) -> tuple[np.ndarray, ...]:
    return (
        image,
        cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE),
        cv2.rotate(image, cv2.ROTATE_180),
        cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE),
    )


def _views(image: np.ndarray) -> tuple[np.ndarray, ...]:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(2.0, (8, 8)).apply(gray)
    boosted = cv2.cvtColor(clahe, cv2.COLOR_GRAY2RGB)
    blurred = cv2.GaussianBlur(image, (0, 0), 0.7)
    return image, boosted, blurred


def _detect(detector: object, image: np.ndarray) -> tuple[str, np.ndarray | None]:
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    result = detector.detectAndDecode(bgr)
    text = result[0] if result else ""
    points = None if len(result) < 2 or result[1] is None else np.asarray(result[1], np.float32).reshape(-1, 2)
    return str(text or ""), points


def _detectors() -> tuple[object, ...]:
    detectors: list[object] = [cv2.QRCodeDetector()]
    try:
        detectors.append(cv2.QRCodeDetectorAruco())
    except Exception:
        return tuple(detectors)
    return tuple(detectors)


def _header_from_text(text: str) -> DecodedQrHeader | None:
    cleaned = "".join(text.split())
    if not cleaned:
        return None
    try:
        blob = base64.b64decode(cleaned, validate=False)
        return decode_header_bytes(blob)
    except (ValueError, struct.error, binascii.Error):
        return None
