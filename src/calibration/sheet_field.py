import zlib

from calibration.sheet_spec import TAG_COLUMNS, TAG_ROWS, Patch

UNWRITTEN = -1


def cell_mm(cell_px: int) -> float:
    return cell_px * 25.4 / 720.0


def tag_quiet_mm(tag_mm: float) -> float:
    return max(0.6, tag_mm * 0.22)


def tag_centers(patch: Patch) -> dict[int, tuple[float, float]]:
    """Tag centres on a TAG_COLUMNS x TAG_ROWS mesh at the patch pitch, centred in the patch."""
    left = patch.x_mm + (patch.w_mm - (TAG_COLUMNS - 1) * patch.pitch_mm) / 2.0
    top = patch.y_mm + (patch.h_mm - (TAG_ROWS - 1) * patch.pitch_mm) / 2.0
    points = [
        (left + col * patch.pitch_mm, top + row * patch.pitch_mm)
        for row in range(TAG_ROWS) for col in range(TAG_COLUMNS)
    ]
    return {tag_id: point for tag_id, point in zip(patch.tag_ids, points, strict=True)}


def field_rect(patch: Patch) -> tuple[float, float, float, float]:
    centers = list(tag_centers(patch).values())
    x0 = min(point[0] for point in centers)
    y0 = min(point[1] for point in centers)
    return x0, y0, (TAG_COLUMNS - 1) * patch.pitch_mm, (TAG_ROWS - 1) * patch.pitch_mm


def cell_counts(patch: Patch) -> tuple[int, int]:
    _x, _y, width, height = field_rect(patch)
    step = cell_mm(patch.cell_px)
    if step <= 0:
        return 0, 0
    return int(width / step), int(height / step)


def symbol_grid(patch: Patch) -> list[list[int]]:
    """Seeded expected symbols; cells under a tag or its quiet zone are UNWRITTEN."""
    cols, rows = cell_counts(patch)
    state = zlib.crc32(patch.name.encode()) & 0x7FFFFFFF or 1
    blocked = _blocked_cells(patch)
    grid: list[list[int]] = []
    for row in range(rows):
        line: list[int] = []
        for col in range(cols):
            state = (1103515245 * state + 12345) & 0x7FFFFFFF
            line.append(UNWRITTEN if (row, col) in blocked else state % patch.symbols)
        grid.append(line)
    return grid


def written_cells(patch: Patch) -> int:
    return sum(symbol != UNWRITTEN for line in symbol_grid(patch) for symbol in line)


def _blocked_cells(patch: Patch) -> set[tuple[int, int]]:
    cols, rows = cell_counts(patch)
    x0, y0, _width, _height = field_rect(patch)
    step = cell_mm(patch.cell_px)
    reach = patch.tag_mm / 2.0 + tag_quiet_mm(patch.tag_mm)
    blocked: set[tuple[int, int]] = set()
    for cx, cy in tag_centers(patch).values():
        for row in range(rows):
            for col in range(cols):
                left, top = x0 + col * step, y0 + row * step
                if left < cx + reach and left + step > cx - reach and top < cy + reach and top + step > cy - reach:
                    blocked.add((row, col))
    return blocked
