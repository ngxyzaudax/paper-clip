import base64
import binascii
import struct

import cv2
import numpy as np

from common.format_spec import qr_module_count
from serialization.decode.errors import DecodeError
from serialization.decode.qr_bend import bent_qr_retry
from serialization.encode.qr_header import DecodedQrHeader, decode_header_bytes

_MODULE_PX = 8
_QUIET_PX = 16


def read_qr_header(image: np.ndarray) -> tuple[np.ndarray, DecodedQrHeader, np.ndarray | None]:
    detectors = _detectors()
    found = _first_header(image, (image,), detectors) or _window_header(image, detectors)
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


def _window_header(
    image: np.ndarray, detectors: tuple[object, ...],
) -> tuple[np.ndarray, DecodedQrHeader, np.ndarray | None] | None:
    for x_px, y_px, crop in _windows(image):
        found = _first_header(image, (crop,), detectors)
        if found is None:
            continue
        _rotated, header, points = found
        if points is None:
            continue
        return image, header, points + np.array([x_px, y_px], np.float32)
    return None


def _windows(image: np.ndarray) -> tuple[tuple[int, int, np.ndarray], ...]:
    height, width = image.shape[:2]
    side = min(height, width, max(1600, int(min(height, width) * 0.45)))
    center = (max(0, (width - side) // 2), max(0, (height - side) // 2))
    corners = (
        (0, 0),
        (max(0, width - side), 0),
        (0, max(0, height - side)),
        (max(0, width - side), max(0, height - side)),
    )
    origins = (center, *(item for item in corners if item != center))
    return tuple((x_px, y_px, image[y_px:y_px + side, x_px:x_px + side]) for x_px, y_px in origins)


def _detect(detector: object, image: np.ndarray) -> tuple[str, np.ndarray | None]:
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    result = detector.detectAndDecode(bgr)
    text = str(result[0] or "") if result else ""
    points = None if not result or len(result) < 2 or result[1] is None else np.asarray(result[1], np.float32).reshape(-1, 2)
    if text or points is None or len(points) != 4:
        return text, points
    return _text_with_quiet_zone(detector, bgr, points) or text, points


def _text_with_quiet_zone(detector: object, image: np.ndarray, points: np.ndarray) -> str:
    side = qr_module_count() * _MODULE_PX
    dest = np.array([[0, 0], [side - 1, 0], [side - 1, side - 1], [0, side - 1]], np.float32)
    warped = cv2.warpPerspective(image, cv2.getPerspectiveTransform(points, dest), (side, side), flags=cv2.INTER_CUBIC)
    padded = cv2.copyMakeBorder(warped, _QUIET_PX, _QUIET_PX, _QUIET_PX, _QUIET_PX, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    result = detector.detectAndDecode(padded)
    return str(result[0] or "") if result else ""


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
