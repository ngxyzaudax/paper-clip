from common.legacy_layout import APRILTAG_36H11_ID_COUNT, APRILTAG_MESH_N
from common.layout_spatial import UsableLayout, tag_paste_top_left


def tag_box_overlaps_rect(
    cx: float, cy: float, fp: int, rx: int, ry: int, rw: int, rh: int,
) -> bool:
    half = fp / 2.0
    tlx = cx - half
    tly = cy - half
    brx = cx + half
    bry = cy + half
    return not (brx <= rx or tlx >= rx + rw or bry <= ry or tly >= ry + rh)


def tag_mesh_centers(
    uw: int, uh: int, fp: int, clearance: int, n: int,
) -> list[tuple[float, float]]:
    h = fp / 2.0 + float(clearance)
    span_x = float(uw) - 2.0 * h
    span_y = float(uh) - 2.0 * h
    if n <= 0:
        return []
    if n == 1:
        return [(float(uw) / 2.0, float(uh) / 2.0)]
    out: list[tuple[float, float]] = []
    for i in range(n):
        ti = float(i) / float(n - 1)
        for j in range(n):
            tj = float(j) / float(n - 1)
            cx = h + span_x * tj
            cy = h + span_y * ti
            out.append((cx, cy))
    return out


def mesh_tag_paste_tuples_for_layout(
    lay: UsableLayout,
    cell: int,
    clearance: int,
) -> list[tuple[int, int, int, int]]:
    uw, uh, fp = lay.uw, lay.uh, lay.fp
    n = APRILTAG_MESH_N
    centers = tag_mesh_centers(uw, uh, fp, clearance, n)
    qx, qy, qs = lay.qx, lay.qy, lay.qr_s
    out: list[tuple[int, int, int, int]] = []
    idx = 0
    for i in range(n):
        for j in range(n):
            cx, cy = centers[idx]
            idx += 1
            if tag_box_overlaps_rect(cx, cy, fp, qx, qy, qs, qs):
                continue
            lx, ty = tag_paste_top_left(cx, cy, fp, cell)
            tid = (i * n + j) % APRILTAG_36H11_ID_COUNT
            out.append((lx, ty, tid, fp))
    return out
