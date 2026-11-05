import base64
import binascii
import struct

import cv2
import numpy as np

from common.format_spec import qr_module_count
from serialization.encode.header_bytes import DecodedQrHeader, decode_header_bytes

_MODULE_PX = 8
_QUIET_PX = 16


def header_from_text(text: str) -> DecodedQrHeader | None:
    cleaned = "".join(text.split())
    if not cleaned:
        return None
    try:
        return decode_header_bytes(base64.b64decode(cleaned, validate=False))
    except (ValueError, struct.error, binascii.Error):
        return None


def detectors() -> tuple[object, ...]:
    found: list[object] = [cv2.QRCodeDetector()]
    try:
        found.append(cv2.QRCodeDetectorAruco())
    except Exception:
        return tuple(found)
    return tuple(found)


def rotations(image: np.ndarray) -> tuple[np.ndarray, ...]:
    return (
        image,
        cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE),
        cv2.rotate(image, cv2.ROTATE_180),
        cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE),
    )


def views(image: np.ndarray) -> tuple[np.ndarray, ...]:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    boosted = cv2.cvtColor(cv2.createCLAHE(2.0, (8, 8)).apply(gray), cv2.COLOR_GRAY2RGB)
    blurred = cv2.GaussianBlur(image, (0, 0), 0.7)
    return image, boosted, blurred


def detect(detector: object, image: np.ndarray) -> tuple[str, np.ndarray | None]:
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    result = detector.detectAndDecode(bgr)
    text = str(result[0] or "") if result else ""
    points = None if not result or len(result) < 2 or result[1] is None else np.asarray(result[1], np.float32).reshape(-1, 2)
    if text or points is None or len(points) != 4:
        return text, points
    return _text_with_quiet_zone(detector, bgr, points) or text, points


def first_header(
    rotated: np.ndarray, seen: tuple[np.ndarray, ...], found: tuple[object, ...],
) -> tuple[np.ndarray, DecodedQrHeader, np.ndarray | None] | None:
    for view in seen:
        for detector in found:
            text, points = detect(detector, view)
            header = header_from_text(text)
            if header is not None:
                return rotated, header, points
    return None


def window_header(
    image: np.ndarray, found: tuple[object, ...],
) -> tuple[np.ndarray, DecodedQrHeader, np.ndarray | None] | None:
    for x_px, y_px, crop in _windows(image):
        hit = first_header(image, (crop,), found)
        if hit is None or hit[2] is None:
            continue
        _rotated, header, points = hit
        return image, header, points + np.array([x_px, y_px], np.float32)
    return None


def _text_with_quiet_zone(detector: object, image: np.ndarray, points: np.ndarray) -> str:
    side = qr_module_count() * _MODULE_PX
    dest = np.array([[0, 0], [side - 1, 0], [side - 1, side - 1], [0, side - 1]], np.float32)
    warped = cv2.warpPerspective(image, cv2.getPerspectiveTransform(points, dest), (side, side), flags=cv2.INTER_CUBIC)
    padded = cv2.copyMakeBorder(warped, _QUIET_PX, _QUIET_PX, _QUIET_PX, _QUIET_PX, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    result = detector.detectAndDecode(padded)
    return str(result[0] or "") if result else ""


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
