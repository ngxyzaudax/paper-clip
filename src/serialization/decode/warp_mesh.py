import numpy as np

from common.geometry import PageGeometry, tag_center_xy
from serialization.decode.errors import DecodeError
from serialization.decode.warp_math import homography, order_quad, project, qr_code_corners, vstack, warp_global
from serialization.decode.warp_tps import warp_tps

_QR_MATCH_PX = 8.0


def warp_page(
    image: np.ndarray,
    geometry: PageGeometry,
    detected: dict[int, np.ndarray],
    qr_points: np.ndarray | None,
) -> np.ndarray:
    src, dst = _tag_pairs(geometry, detected)
    border = _corner_pairs(geometry, detected)
    bsrc, bdst = (src, dst) if border is None else border
    anchors = (np.zeros((0, 2), np.float32), np.zeros((0, 2), np.float32))
    if qr_points is not None and len(qr_points) == 4 and len(bsrc) >= 4:
        anchors = _match_qr(bsrc, bdst, qr_points, geometry)
        bsrc, bdst = vstack(bsrc, anchors[0]), vstack(bdst, anchors[1])
    elif qr_points is not None and len(qr_points) == 4 and len(src) < 4:
        src, dst = vstack(src, order_quad(qr_points)), vstack(dst, qr_code_corners(geometry))
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


def _match_qr(
    src: np.ndarray, dst: np.ndarray, qr_points: np.ndarray, geometry: PageGeometry,
) -> tuple[np.ndarray, np.ndarray]:
    empty = (np.zeros((0, 2), np.float32), np.zeros((0, 2), np.float32))
    try:
        inverse = np.linalg.inv(homography(src, dst))
    except np.linalg.LinAlgError:
        return empty
    ideal = qr_code_corners(geometry)
    projected = np.stack([project(inverse, point) for point in ideal])
    used: set[int] = set()
    extra_src: list[np.ndarray] = []
    extra_dst: list[np.ndarray] = []
    for guess, dest in zip(projected, ideal):
        dists = np.linalg.norm(qr_points - guess, axis=1)
        index = int(np.argmin(dists))
        if index in used or float(dists[index]) > _QR_MATCH_PX:
            continue
        used.add(index)
        extra_src.append(qr_points[index])
        extra_dst.append(dest)
    if len(extra_src) < 4:
        return empty
    return np.stack(extra_src).astype(np.float32), np.stack(extra_dst).astype(np.float32)
