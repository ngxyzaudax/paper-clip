import logging
from typing import Any

import apriltag
import cv2
import numpy as np

from common.apriltag_markers import CORNER_TAG_IDS, ordered_corner_centers
from common.config import DOWNSCALE_MAX_DIM
from common.types import Point

logger = logging.getLogger(__name__)

_DETECTOR: apriltag.apriltag | None = None


def _get_detector() -> apriltag.apriltag:
    global _DETECTOR
    if _DETECTOR is None:
        _DETECTOR = apriltag.apriltag("tag36h11")
    return _DETECTOR


def _apriltag_lib_detect(gray: np.ndarray) -> list[dict[str, Any]]:
    return _get_detector().detect(gray)


def _opencv_corners_to_detection(mid: int, pts: np.ndarray) -> dict[str, Any]:
    tl, tr, br, bl = pts[0], pts[1], pts[2], pts[3]
    center = pts.mean(axis=0).astype(np.float32)
    lb_rb_rt_lt = np.array([bl, br, tr, tl], dtype=np.float32)
    return {"id": mid, "center": center, "lb-rb-rt-lt": lb_rb_rt_lt}


def _opencv_aruco_detect(gray: np.ndarray) -> list[dict[str, Any]]:
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    params = cv2.aruco.DetectorParameters()
    try:
        detector = cv2.aruco.ArucoDetector(dictionary, params)
        corners, ids, _ = detector.detectMarkers(gray)
    except AttributeError:
        corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=params)
    if ids is None or len(ids) == 0:
        return []
    out: list[dict[str, Any]] = []
    for i in range(len(ids)):
        mid = int(ids[i].flat[0])
        if mid not in CORNER_TAG_IDS:
            continue
        out.append(_opencv_corners_to_detection(mid, corners[i][0].astype(np.float32)))
    return out


def _scale_detection(d: dict[str, Any], sx: float, sy: float) -> dict[str, Any]:
    c = np.asarray(d["center"], dtype=np.float64)
    pts = np.array(d["lb-rb-rt-lt"], dtype=np.float32)
    return {
        "id": d["id"],
        "center": np.array([c[0] * sx, c[1] * sy], dtype=np.float32),
        "lb-rb-rt-lt": (pts * np.array([sx, sy], dtype=np.float32)),
    }


def _merge_corner_detections(merged: dict[int, dict[str, Any]], dets: list[dict[str, Any]]) -> None:
    for d in dets:
        mid = int(d["id"])
        if mid not in CORNER_TAG_IDS:
            continue
        if mid not in merged:
            merged[mid] = d


def detect_apriltags(image: np.ndarray) -> list[dict[str, Any]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    h, w = gray.shape[:2]
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray_eq = clahe.apply(gray)
    merged: dict[int, dict[str, Any]] = {}

    for g in (gray_eq, gray):
        _merge_corner_detections(merged, _apriltag_lib_detect(g))
    for g in (gray_eq, gray):
        _merge_corner_detections(merged, _opencv_aruco_detect(g))

    max_dim = max(h, w)
    if len(merged) < 4 and max_dim > DOWNSCALE_MAX_DIM:
        scale = DOWNSCALE_MAX_DIM / max_dim
        nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
        g_small = cv2.resize(gray, (nw, nh), interpolation=cv2.INTER_AREA)
        g_eq_small = clahe.apply(g_small)
        sx, sy = w / nw, h / nh
        for g in (g_eq_small, g_small):
            for d in _apriltag_lib_detect(g) + _opencv_aruco_detect(g):
                mid = int(d["id"])
                if mid not in CORNER_TAG_IDS or mid in merged:
                    continue
                merged[mid] = _scale_detection(d, sx, sy)

    if len(merged) < 4 and max_dim > 3200:
        nw, nh = max(1, int(round(w * 0.5))), max(1, int(round(h * 0.5)))
        g_half = cv2.resize(gray, (nw, nh), interpolation=cv2.INTER_AREA)
        g_half_eq = clahe.apply(g_half)
        sx, sy = w / nw, h / nh
        for g in (g_half_eq, g_half):
            for d in _apriltag_lib_detect(g) + _opencv_aruco_detect(g):
                mid = int(d["id"])
                if mid not in CORNER_TAG_IDS or mid in merged:
                    continue
                merged[mid] = _scale_detection(d, sx, sy)

    return list(merged.values())


def tag_corners_from_detections(
    detections: list[dict[str, Any]],
) -> dict[int, np.ndarray]:
    return {
        int(d["id"]): np.array(d["lb-rb-rt-lt"], dtype=np.float32)
        for d in detections
        if int(d["id"]) in CORNER_TAG_IDS
    }


def detect_markers_with_corners(
    image: np.ndarray,
) -> tuple[list[tuple[float, float]], dict[int, np.ndarray] | None]:
    detections = detect_apriltags(image)
    relevant = [d for d in detections if int(d["id"]) in CORNER_TAG_IDS]
    corners = ordered_corner_centers(relevant)
    if corners is None:
        ids = [int(d["id"]) for d in relevant]
        logger.warning("Detected %d/4 corner tags (IDs: %s)", len(ids), ids)
        return [], None
    markers = [(float(c[0]), float(c[1])) for c in corners]
    tc = tag_corners_from_detections(detections)
    tag_corners = tc if len(tc) >= 3 else None
    logger.debug("All 4 AprilTag corners resolved (IDs: %s)", [d["id"] for d in relevant])
    return markers, tag_corners


def detect_finder_patterns(image: np.ndarray) -> list[Point]:
    markers, _ = detect_markers_with_corners(image)
    return markers


def extract_tag_corners(
    image: np.ndarray, detections: list[dict[str, Any]] | None = None,
) -> dict[int, np.ndarray]:
    dets = detections if detections is not None else detect_apriltags(image)
    return tag_corners_from_detections(dets)
