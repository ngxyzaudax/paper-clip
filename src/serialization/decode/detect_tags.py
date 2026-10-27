import cv2
import numpy as np

_DETECTOR: cv2.aruco.ArucoDetector | None = None


def detect_tags(image: np.ndarray, expected_ids: set[int]) -> dict[int, np.ndarray]:
    found = _detect_once(image, expected_ids)
    if len(found) >= len(expected_ids) and found:
        return found
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    boosted = cv2.cvtColor(cv2.createCLAHE(2.0, (8, 8)).apply(gray), cv2.COLOR_GRAY2RGB)
    for tag_id, center in _detect_once(boosted, expected_ids).items():
        found.setdefault(tag_id, center)
    return found


def _detect_once(image: np.ndarray, expected_ids: set[int]) -> dict[int, np.ndarray]:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
    corners, ids, _rejected = _detector().detectMarkers(gray)
    found: dict[int, np.ndarray] = {}
    if ids is None:
        return found
    for corner, tag_id in zip(corners, ids.flatten().tolist()):
        if int(tag_id) not in expected_ids or int(tag_id) in found:
            continue
        found[int(tag_id)] = np.mean(np.asarray(corner, np.float32).reshape(-1, 2), axis=0)
    return found


def _detector() -> cv2.aruco.ArucoDetector:
    global _DETECTOR
    if _DETECTOR is not None:
        return _DETECTOR
    params = cv2.aruco.DetectorParameters()
    params.minMarkerPerimeterRate = 0.004
    params.maxMarkerPerimeterRate = 4.0
    params.adaptiveThreshWinSizeMin = 3
    params.adaptiveThreshWinSizeMax = 33
    params.adaptiveThreshWinSizeStep = 4
    params.minCornerDistanceRate = 0.01
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    _DETECTOR = cv2.aruco.ArucoDetector(dictionary, params)
    return _DETECTOR
