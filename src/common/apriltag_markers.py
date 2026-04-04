from collections.abc import Sequence

import cv2
import numpy as np
from PIL import Image

from common.tag_detection import TagDetection

APRILTAG_FAMILY = "tag36h11"
APRILTAG_CV2_DICT = cv2.aruco.DICT_APRILTAG_36h11

TL_TAG_ID = 0
TR_TAG_ID = 1
BL_TAG_ID = 2
BR_TAG_ID = 3

CORNER_TAG_IDS = (TL_TAG_ID, TR_TAG_ID, BL_TAG_ID, BR_TAG_ID)

TAG_ID_TO_CORNER = {
    TL_TAG_ID: "tl",
    TR_TAG_ID: "tr",
    BL_TAG_ID: "bl",
    BR_TAG_ID: "br",
}


def _aruco_dict() -> cv2.aruco.Dictionary:
    return cv2.aruco.getPredefinedDictionary(APRILTAG_CV2_DICT)


def render_apriltag(tag_id: int, size_px: int) -> Image.Image:
    marker = cv2.aruco.generateImageMarker(_aruco_dict(), tag_id, size_px)
    return Image.fromarray(marker).convert("RGB")


def ordered_corner_centers(
    detections: Sequence[TagDetection],
) -> list[tuple[float, float]] | None:
    """Return tag centers in [TL, TR, BL, BR] order, or None if <3 found."""
    by_id = {d.tag_id: d for d in detections if d.tag_id in CORNER_TAG_IDS}
    if len(by_id) < 3:
        return None
    centers: list[tuple[float, float] | None] = [None, None, None, None]
    for idx, tag_id in enumerate(CORNER_TAG_IDS):
        if tag_id in by_id:
            c = by_id[tag_id].center
            centers[idx] = (float(c[0]), float(c[1]))
    if sum(c is not None for c in centers) == 3:
        centers = _infer_fourth_corner(centers)
    return centers if all(c is not None for c in centers) else None


def _infer_fourth_corner(
    centers: list[tuple[float, float] | None],
) -> list[tuple[float, float] | None]:
    """Infer missing corner using parallelogram property: TL + BR = TR + BL."""
    known = {i: c for i, c in enumerate(centers) if c is not None}
    if len(known) != 3:
        return centers
    missing = next(i for i in range(4) if i not in known)
    diagonal_partner = {0: 3, 3: 0, 1: 2, 2: 1}
    partner = diagonal_partner[missing]
    others = [c for i, c in known.items() if i != partner]
    pp = known[partner]
    inferred = (others[0][0] + others[1][0] - pp[0], others[0][1] + others[1][1] - pp[1])
    result = list(centers)
    result[missing] = inferred
    return result
