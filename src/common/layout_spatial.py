from typing import NamedTuple

from common.config import FIDUCIAL_DPI


def print_px_to_fiducial_px(px: int, print_dpi: int, fiducial_dpi: int) -> int:
    return (px * fiducial_dpi + print_dpi // 2) // print_dpi


def fiducial_px_to_print_px(px: int, print_dpi: int, fiducial_dpi: int) -> int:
    return (px * print_dpi + fiducial_dpi // 2) // fiducial_dpi


class UsableLayout(NamedTuple):
    uw: int
    uh: int
    cell: int
    fp: int
    qr_s: int
    strip_h: int
    qx: int
    qy: int


def center_qr_size_px(uw: int, uh: int, cell: int, print_dpi: int) -> int:
    fd = FIDUCIAL_DPI
    uw_f = print_px_to_fiducial_px(uw, print_dpi, fd)
    uh_f = print_px_to_fiducial_px(uh, print_dpi, fd)
    cell_f = max(1, print_px_to_fiducial_px(cell, print_dpi, fd))
    lo_f = (200 * fd + print_dpi // 2) // print_dpi
    hi_f = (520 * fd + print_dpi // 2) // print_dpi
    s = max(lo_f, min(hi_f, int(min(uw_f, uh_f) * 0.21)))
    s = max(8 * cell_f, (s // cell_f) * cell_f)
    s = max(4 * cell_f, s)
    qr = fiducial_px_to_print_px(s, print_dpi, fd)
    qr = max(4 * cell, (qr // cell) * cell)
    return max(4 * cell, qr)


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
    uw: int, uh: int, cell: int, fp: int, strip_h: int, print_dpi: int,
) -> UsableLayout:
    qr_s = center_qr_size_px(uw, uh, cell, print_dpi)
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
    from common.apriltag_layout import mesh_tag_paste_tuples_for_layout

    uw, uh, qr_s, strip_h = layout.uw, layout.uh, layout.qr_s, layout.strip_h
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
    for lx, ly, _, fp in mesh_tag_paste_tuples_for_layout(lay, cell, clearance):
        rects.append(expand_rect_clamped(lx, ly, fp, fp, clearance, uw, uh))
    return rects


def tag_paste_top_left(tcx: float, tcy: float, fp: int, cell: int) -> tuple[int, int]:
    lx = int(round(tcx - fp / 2.0))
    ly = int(round(tcy - fp / 2.0))
    lx = (lx // cell) * cell
    ly = (ly // cell) * cell
    return lx, ly


def _first_col_center_px_ge(rx: int, cell: int, cols: int) -> int | None:
    for c in range(cols):
        if c * cell + cell // 2 >= rx:
            return c
    return None


def _last_col_center_px_lt(rx_ex: int, cell: int, cols: int) -> int | None:
    for c in range(cols - 1, -1, -1):
        if c * cell + cell // 2 < rx_ex:
            return c
    return None


def _first_row_center_py_ge(ry: int, cell: int, rows: int) -> int | None:
    for r in range(rows):
        if r * cell + cell // 2 >= ry:
            return r
    return None


def _last_row_center_py_lt(ry_ex: int, cell: int, rows: int) -> int | None:
    for r in range(rows - 1, -1, -1):
        if r * cell + cell // 2 < ry_ex:
            return r
    return None


def _forbidden_cell_mask(
    cols: int, rows: int, cell: int, forbidden: list[tuple[int, int, int, int]],
) -> bytearray:
    n = cols * rows
    bad = bytearray(n)
    if not forbidden:
        return bad
    for rx, ry, rw, rh in forbidden:
        rx_ex = rx + rw
        ry_ex = ry + rh
        c0 = _first_col_center_px_ge(rx, cell, cols)
        if c0 is None:
            continue
        c1 = _last_col_center_px_lt(rx_ex, cell, cols)
        if c1 is None or c1 < c0:
            continue
        r0 = _first_row_center_py_ge(ry, cell, rows)
        if r0 is None:
            continue
        r1 = _last_row_center_py_lt(ry_ex, cell, rows)
        if r1 is None or r1 < r0:
            continue
        for row in range(r0, r1 + 1):
            base = row * cols
            for col in range(c0, c1 + 1):
                bad[base + col] = 1
    return bad


def valid_cells_row_major(
    cols: int, rows: int, cell: int, forbidden: list[tuple[int, int, int, int]],
) -> list[tuple[int, int]]:
    bad = _forbidden_cell_mask(cols, rows, cell, forbidden)
    n = cols * rows
    vc = n - sum(bad)
    if vc == 0:
        return []
    out: list[tuple[int, int]] = [(0, 0)] * vc
    idx = 0
    for row in range(rows):
        base = row * cols
        for col in range(cols):
            if not bad[base + col]:
                out[idx] = (row, col)
                idx += 1
    return out


def count_valid_cells_row_major(
    cols: int, rows: int, cell: int, forbidden: list[tuple[int, int, int, int]],
) -> int:
    n = cols * rows
    if not forbidden:
        return n
    bad = _forbidden_cell_mask(cols, rows, cell, forbidden)
    return n - sum(bad)
