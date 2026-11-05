from typing import NamedTuple

CELL_PX = 16
STRIP_ROWS = 64
HALO = 2


class Strip(NamedTuple):
    y0: int
    y1: int
    row0: int
    row1: int


def strips(rows: int) -> tuple[Strip, ...]:
    return tuple(_strip(rows, start) for start in range(0, rows, STRIP_ROWS))


def groups(items: tuple[Strip, ...]) -> tuple[tuple[Strip, ...], ...]:
    order: list[int] = []
    buckets: dict[int, list[Strip]] = {}
    for item in items:
        height = strip_height(item)
        if height not in buckets:
            order.append(height)
            buckets[height] = []
        buckets[height].append(item)
    return tuple(tuple(buckets[height]) for height in order)


def strip_height(strip: Strip) -> int:
    return strip.y1 - strip.y0


def output_row(strip: Strip) -> int:
    return (strip.row0 * CELL_PX - strip.y0) // CELL_PX


def _strip(rows: int, start: int) -> Strip:
    stop = min(rows, start + STRIP_ROWS)
    y0 = max(0, (start - HALO) * CELL_PX)
    y1 = min(rows * CELL_PX, (stop + HALO) * CELL_PX)
    return Strip(y0, y1, start, stop)
