from collections.abc import Mapping
from typing import NamedTuple

import numpy as np


class TagDetection(NamedTuple):
    tag_id: int
    center: np.ndarray
    corners_lb_rb_rt_lt: np.ndarray


def _from_tl_tr_br_bl_corners(
    tag_id: int, center: object, corners: object,
) -> TagDetection | None:
    pts = np.asarray(corners, dtype=np.float32).reshape(-1, 2)
    if pts.shape[0] != 4:
        return None
    tl, tr, br, bl = pts[0], pts[1], pts[2], pts[3]
    lb_rb_rt_lt = np.array([bl, br, tr, tl], dtype=np.float32)
    c = np.asarray(center, dtype=np.float32).reshape(-1)[:2]
    return TagDetection(tag_id, c, lb_rb_rt_lt)


def tag_detection_from_detector_item(item: object) -> TagDetection | None:
    if isinstance(item, TagDetection):
        return item
    if isinstance(item, Mapping):
        m: Mapping[str, object] = item
        tid_raw = m.get("id", m.get("tag_id"))
        center = m.get("center")
        if tid_raw is None or center is None:
            return None
        tid = int(tid_raw)
        if "lb-rb-rt-lt" in m:
            c = np.asarray(center, dtype=np.float32).reshape(-1)[:2]
            pts = np.asarray(m["lb-rb-rt-lt"], dtype=np.float32)
            if pts.size != 8:
                return None
            return TagDetection(tid, c, pts.reshape(4, 2))
        corners = m.get("corners")
        if corners is not None:
            return _from_tl_tr_br_bl_corners(tid, center, corners)
        return None
    tid = getattr(item, "tag_id", None)
    center = getattr(item, "center", None)
    corners = getattr(item, "corners", None)
    if tid is None or center is None or corners is None:
        return None
    return _from_tl_tr_br_bl_corners(int(tid), center, corners)


def opencv_marker_to_tag_detection(mid: int, pts: np.ndarray) -> TagDetection:
    tl, tr, br, bl = pts[0], pts[1], pts[2], pts[3]
    center = pts.mean(axis=0).astype(np.float32)
    lb_rb_rt_lt = np.array([bl, br, tr, tl], dtype=np.float32)
    return TagDetection(mid, center, lb_rb_rt_lt)
