import numpy as np

from common.geometry import PageGeometry, tag_center_xy
from serialization.decode.errors import DecodeError
from serialization.decode.qr_anchor import fallback_qr_quad, matched_qr_anchors
from serialization.decode.warp_math import homography, vstack, warp_global
from serialization.decode.warp_tps import warp_tps


def warp_page(
    image: np.ndarray,
    geometry: PageGeometry,
    detected: dict[int, np.ndarray],
    qr_points: np.ndarray | None,
    extra_points: tuple[np.ndarray, ...] = (),
) -> np.ndarray:
    src, dst = _tag_pairs(geometry, detected)
    border = _corner_pairs(geometry, detected)
    bsrc, bdst = (src, dst) if border is None else border
    quads = _quads(qr_points, extra_points)
    anchors = (np.zeros((0, 2), np.float32), np.zeros((0, 2), np.float32))
    if quads and len(bsrc) >= 4:
        anchors = matched_qr_anchors(bsrc, bdst, quads, geometry)
        if len(anchors[0]):
            bsrc, bdst = vstack(bsrc, anchors[0]), vstack(bdst, anchors[1])
    elif quads and len(src) < 4:
        quad_src, quad_dst = fallback_qr_quad(quads, geometry, detected)
        src, dst = vstack(src, quad_src), vstack(dst, quad_dst)
        bsrc, bdst = src, dst
    if len(src) < 4:
        raise DecodeError(f"only {len(detected)} alignment tags found; need at least 4")
    matrix = homography(bsrc, bdst)
    if len(detected) < 4 or abs(float(np.linalg.det(matrix))) < 1e-12:
        return warp_global(image, matrix, geometry.page_w, geometry.page_h)
    return warp_tps(
        image, np.linalg.inv(matrix), vstack(dst, anchors[1]), vstack(src, anchors[0]),
        geometry.page_w, geometry.page_h,
    )


def _quads(primary: np.ndarray | None, extra: tuple[np.ndarray, ...]) -> tuple[np.ndarray, ...]:
    raw = [primary, *extra] if primary is not None else list(extra)
    quads = [np.asarray(item, np.float32).reshape(-1, 2) for item in raw]
    return tuple(item for item in quads if len(item) == 4)


def _tag_pairs(geometry: PageGeometry, detected: dict[int, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    src: list[np.ndarray] = []
    dst: list[np.ndarray] = []
    for tag in geometry.tags:
        if tag.tag_id not in detected:
            continue
        src.append(np.asarray(detected[tag.tag_id], np.float32))
        dst.append(np.asarray(tag_center_xy(geometry, tag), np.float32))
    if not src:
        return np.zeros((0, 2), np.float32), np.zeros((0, 2), np.float32)
    return np.stack(src), np.stack(dst)


def _corner_pairs(
    geometry: PageGeometry, detected: dict[int, np.ndarray],
) -> tuple[np.ndarray, np.ndarray] | None:
    corners = {
        0,
        geometry.tag_cols - 1,
        (geometry.tag_rows - 1) * geometry.tag_cols,
        geometry.tag_rows * geometry.tag_cols - 1,
    }
    src: list[np.ndarray] = []
    dst: list[np.ndarray] = []
    for tag in geometry.tags:
        if tag.tag_id not in corners or tag.tag_id not in detected:
            continue
        src.append(np.asarray(detected[tag.tag_id], np.float32))
        dst.append(np.asarray(tag_center_xy(geometry, tag), np.float32))
    if len(src) < 4:
        return None
    return np.stack(src), np.stack(dst)
