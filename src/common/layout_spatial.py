from typing import NamedTuple


class UsableLayout(NamedTuple):
    uw: int
    uh: int
    cell: int
    fp: int
    qr_s: int
    strip_h: int
    qx: int
    qy: int


def center_qr_size_px(uw: int, uh: int, cell: int) -> int:
    s = max(200, min(520, int(min(uw, uh) * 0.21)))
    s = max(8 * cell, (s // cell) * cell)
    return max(4 * cell, s)


def qr_top_left_int(uw: int, uh: int, qr_s: int, cell: int) -> tuple[int, int]:
    qx = max(0, (uw - qr_s) // 2)
    qy = max(0, (uh - qr_s) // 2)
    qx = (qx // cell) * cell
    qy = (qy // cell) * cell
    if qx + qr_s > uw:
        qx = max(0, ((uw - qr_s) // cell) * cell)
    if qy + qr_s > uh:
        qy = max(0, ((uh - qr_s) // cell) * cell)
    return qx, qy


def build_usable_layout(
    uw: int, uh: int, cell: int, fp: int, strip_h: int,
) -> UsableLayout:
    qr_s = center_qr_size_px(uw, uh, cell)
    qx, qy = qr_top_left_int(uw, uh, qr_s, cell)
    return UsableLayout(
        uw=uw,
        uh=uh,
        cell=cell,
        fp=fp,
        qr_s=qr_s,
        strip_h=strip_h,
        qx=qx,
        qy=qy,
    )


def corner_tag_centers(
    uw: int, uh: int, fp: int, clearance: int,
) -> list[tuple[float, float]]:
    h = fp / 2.0 + float(clearance)
    return [
        (h, h),
        (uw - h, h),
        (h, uh - h),
        (uw - h, uh - h),
    ]


def flank_tag_centers(layout: UsableLayout, clearance: int) -> list[tuple[float, float]]:
    uw, uh, fp, strip_h = layout.uw, layout.uh, layout.fp, layout.strip_h
    qr_s = layout.qr_s
    fp_h = fp / 2.0
    c = float(clearance)
    cell = float(layout.cell)
    qx0 = float(layout.qx)
    qx1 = float(layout.qx + layout.qr_s)
    gap_qr = max(cell * 2.0, 2.0 * c + float(fp))
    sep = max(c, float(fp))
    tl_trc = c + float(fp)
    left_min_center = tl_trc + sep + fp_h
    right_max_center = float(uw) - tl_trc - sep - fp_h
    left_nom = uw / 4.0
    right_nom = 3.0 * uw / 4.0
    left_x = max(left_nom, left_min_center)
    right_x = min(right_nom, right_max_center)
    if left_x + fp_h + gap_qr > qx0 - c:
        left_x = max(left_min_center, qx0 - gap_qr - fp_h - c)
    if right_x - fp_h - gap_qr < qx1 + c:
        right_x = min(right_max_center, qx1 + gap_qr + fp_h + c)
    if left_x + 2.0 * fp_h >= right_x:
        cx_m = layout.qx + qr_s / 2.0
        half_q = qr_s / 2.0
        hx = max(cell * 2.0, 2.0 * c + float(fp))
        left_x = max(left_min_center, cx_m - half_q - hx - fp_h)
        right_x = min(right_max_center, cx_m + half_q + hx + fp_h)
    y_min = float(strip_h) + fp_h + c
    y_max = float(uh) - fp_h - c
    band_lo = float(uh) / 4.0
    band_hi = 3.0 * float(uh) / 4.0
    y_lo = max(y_min, band_lo)
    y_hi = min(y_max, band_hi)
    if y_hi <= y_lo:
        y_lo, y_hi = y_min, y_max
    span = y_hi - y_lo
    ys = [y_lo + span * i / 2.0 for i in range(3)]
    return [(left_x, y) for y in ys] + [(right_x, y) for y in ys]


def expand_rect_clamped(
    x: int, y: int, w: int, h: int, pad: int, uw: int, uh: int,
) -> tuple[int, int, int, int]:
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(uw, x + w + pad)
    y1 = min(uh, y + h + pad)
    return (x0, y0, x1 - x0, y1 - y0)


def forbidden_rects_usable(
    layout: UsableLayout, clearance: int,
) -> list[tuple[int, int, int, int]]:
    uw, uh, fp, qr_s, strip_h = layout.uw, layout.uh, layout.fp, layout.qr_s, layout.strip_h
    lay = layout
    rects: list[tuple[int, int, int, int]] = []
    if strip_h > 0:
        rects.append(
            expand_rect_clamped(0, 0, uw, strip_h, clearance, uw, uh),
        )
    rects.append(
        expand_rect_clamped(lay.qx, lay.qy, qr_s, qr_s, clearance, uw, uh),
    )
    cell = lay.cell
    for tcx, tcy in corner_tag_centers(uw, uh, fp, clearance):
        lx, ly = tag_paste_top_left(tcx, tcy, fp, cell)
        rects.append(expand_rect_clamped(lx, ly, fp, fp, clearance, uw, uh))
    for tcx, tcy in flank_tag_centers(lay, clearance):
        lx, ly = tag_paste_top_left(tcx, tcy, fp, cell)
        rects.append(expand_rect_clamped(lx, ly, fp, fp, clearance, uw, uh))
    return rects


def tag_paste_top_left(tcx: float, tcy: float, fp: int, cell: int) -> tuple[int, int]:
    lx = int(round(tcx - fp / 2.0))
    ly = int(round(tcy - fp / 2.0))
    lx = (lx // cell) * cell
    ly = (ly // cell) * cell
    return lx, ly


def _inside_rect(px: int, py: int, rx: int, ry: int, rw: int, rh: int) -> bool:
    return rx <= px < rx + rw and ry <= py < ry + rh


def valid_cells_row_major(
    cols: int, rows: int, cell: int, forbidden: list[tuple[int, int, int, int]],
) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for row in range(rows):
        for col in range(cols):
            px = col * cell + cell // 2
            py = row * cell + cell // 2
            bad = any(_inside_rect(px, py, rx, ry, rw, rh) for rx, ry, rw, rh in forbidden)
            if not bad:
                out.append((row, col))
    return out


def count_valid_cells_row_major(
    cols: int, rows: int, cell: int, forbidden: list[tuple[int, int, int, int]],
) -> int:
    n = 0
    for row in range(rows):
        for col in range(cols):
            px = col * cell + cell // 2
            py = row * cell + cell // 2
            bad = any(_inside_rect(px, py, rx, ry, rw, rh) for rx, ry, rw, rh in forbidden)
            if not bad:
                n += 1
    return n
