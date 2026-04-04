import cv2
import numpy as np

from common.apriltag_markers import BL_TAG_ID, BR_TAG_ID, CORNER_TAG_IDS, TL_TAG_ID, TR_TAG_ID
from common.config import PaperClipConfig
from common.page_layout import (
    finder_pattern_size,
    margin_offset,
    page_image_size,
    usable_area_px,
)
from common.types import Point


def _ideal_centers(config: PaperClipConfig) -> np.ndarray:
    fp_size = finder_pattern_size(config)
    mx, my = margin_offset(config)
    usable_w, usable_h = usable_area_px(config)
    half = fp_size // 2
    return np.float32([
        [mx + half, my + half],
        [mx + usable_w - half, my + half],
        [mx + half, my + usable_h - half],
        [mx + usable_w - half, my + usable_h - half],
    ])


def _ideal_tag_corners(config: PaperClipConfig) -> dict[int, np.ndarray]:
    """Return ideal corner points per tag in lb-rb-rt-lt order."""
    fp_size = finder_pattern_size(config)
    mx, my = margin_offset(config)
    usable_w, usable_h = usable_area_px(config)
    half = fp_size // 2
    centers = {
        TL_TAG_ID: (mx + half, my + half),
        TR_TAG_ID: (mx + usable_w - half, my + half),
        BL_TAG_ID: (mx + half, my + usable_h - half),
        BR_TAG_ID: (mx + usable_w - half, my + usable_h - half),
    }
    result = {}
    for tag_id, (cx, cy) in centers.items():
        result[tag_id] = np.float32([
            [cx - half, cy + half],
            [cx + half, cy + half],
            [cx + half, cy - half],
            [cx - half, cy - half],
        ])
    return result


def compute_transform(
    markers: list[Point],
    config: PaperClipConfig,
    tag_corners: dict[int, np.ndarray] | None = None,
) -> np.ndarray:
    if tag_corners and len(tag_corners) >= 3:
        return _compute_overdetermined(tag_corners, config)
    dst_points = _ideal_centers(config)
    src_points = np.float32(markers[:4])
    return _find_homography(src_points, dst_points)


def _compute_overdetermined(
    tag_corners: dict[int, np.ndarray], config: PaperClipConfig
) -> np.ndarray:
    ideal = _ideal_tag_corners(config)
    src_pts = []
    dst_pts = []
    for tag_id in CORNER_TAG_IDS:
        if tag_id in tag_corners:
            src_pts.append(tag_corners[tag_id])
            dst_pts.append(ideal[tag_id])
    src = np.vstack(src_pts).astype(np.float32)
    dst = np.vstack(dst_pts).astype(np.float32)
    return _find_homography(src, dst)


def _find_homography(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    method = cv2.RANSAC if len(src) > 4 else 0
    matrix, _ = cv2.findHomography(src, dst, method)
    if matrix is None:
        raise ValueError(
            "Failed to compute homography: marker positions are degenerate. "
            "The page may be too damaged or markers undetectable."
        )
    return matrix


def apply_deskew(
    image: np.ndarray, transform: np.ndarray, config: PaperClipConfig,
) -> np.ndarray:
    page_w, page_h = page_image_size(config)
    return cv2.warpPerspective(
        image, transform, (page_w, page_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )
