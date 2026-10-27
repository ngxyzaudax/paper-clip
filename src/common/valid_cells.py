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
