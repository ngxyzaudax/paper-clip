from common.geometry_shift import tag_box
from common.geometry_types import HeaderSlot, TagMark
from common.types import Region

CLEARANCE_MM = 3.0

type Opening = tuple[int, int, int, int]


def seat_slots(
    slots: tuple[HeaderSlot, ...],
    tags: tuple[TagMark, ...],
    quiet: int,
    width: int,
    height: int,
    cell: int,
    pad: int,
) -> tuple[HeaderSlot, ...]:
    if not slots:
        return slots
    block = slots[0].block
    openings = _fitting(_openings(tags, quiet, width, height), block.width, block.height, cell, pad)
    seated = _placed(slots, openings, cell, pad)
    if len(seated) != len(slots):
        return slots
    return seated


def _placed(
    slots: tuple[HeaderSlot, ...],
    openings: tuple[Opening, ...],
    cell: int,
    pad: int,
) -> tuple[HeaderSlot, ...]:
    remaining = openings
    seated: list[HeaderSlot] = []
    for slot in slots:
        choice = _closest(slot, remaining)
        placed = None if choice is None else _place(slot, choice, cell, pad)
        if choice is None or placed is None:
            return ()
        seated.append(placed)
        remaining = tuple(item for item in remaining if item != choice)
    return tuple(seated)


def _openings(
    tags: tuple[TagMark, ...],
    quiet: int,
    width: int,
    height: int,
) -> tuple[Opening, ...]:
    boxes = [tag_box(tag, quiet) for tag in tags]
    xs = _gaps(_edges(boxes, 0), width)
    ys = _gaps(_edges(boxes, 1), height)
    return tuple((x0, y0, x1, y1) for x0, x1 in xs for y0, y1 in ys)


def _fitting(
    openings: tuple[Opening, ...],
    block_w: int,
    block_h: int,
    cell: int,
    pad: int,
) -> tuple[Opening, ...]:
    return tuple(
        opening
        for opening in openings
        if _snapped(opening[0], opening[2], block_w, cell, pad) is not None
        and _snapped(opening[1], opening[3], block_h, cell, pad) is not None
    )


def _closest(slot: HeaderSlot, openings: tuple[Opening, ...]) -> Opening | None:
    if not openings:
        return None
    cx = slot.block.x + slot.block.width / 2
    cy = slot.block.y + slot.block.height / 2
    return min(openings, key=lambda box: (_dist(cx, cy, box), box[0], box[1]))


def _place(slot: HeaderSlot, opening: Opening, cell: int, pad: int) -> HeaderSlot | None:
    left = _snapped(opening[0], opening[2], slot.block.width, cell, pad)
    top = _snapped(opening[1], opening[3], slot.block.height, cell, pad)
    if left is None or top is None:
        return None
    return _translate(slot, left - slot.block.x, top - slot.block.y)


def _snapped(start: int, end: int, size: int, cell: int, pad: int) -> int | None:
    lo = _ceil_to(start + pad, cell)
    hi = _floor_to(end - pad - size, cell)
    if lo > hi:
        return None
    ideal = int(round((start + (end - start - size) / 2) / cell)) * cell
    return min(hi, max(lo, ideal))


def _edges(boxes: list[tuple[int, int, int, int]], axis: int) -> tuple[tuple[int, int], ...]:
    return tuple(sorted({(box[axis], box[axis] + box[axis + 2]) for box in boxes}))


def _gaps(spans: tuple[tuple[int, int], ...], limit: int) -> tuple[tuple[int, int], ...]:
    cursor = 0
    found: list[tuple[int, int]] = []
    for start, end in spans:
        start, end = _clamp(start, limit), _clamp(end, limit)
        if start > cursor:
            found.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < limit:
        found.append((cursor, limit))
    return tuple(found)


def _translate(slot: HeaderSlot, dx: int, dy: int) -> HeaderSlot:
    return HeaderSlot(_shift(slot.qr, dx, dy), _shift(slot.calibration, dx, dy), _shift(slot.block, dx, dy))


def _shift(region: Region, dx: int, dy: int) -> Region:
    return region._replace(x=region.x + dx, y=region.y + dy)


def _ceil_to(value: int, cell: int) -> int:
    return ((value + cell - 1) // cell) * cell


def _floor_to(value: int, cell: int) -> int:
    return (value // cell) * cell


def _clamp(value: int, limit: int) -> int:
    return min(max(value, 0), limit)


def _dist(cx: float, cy: float, box: Opening) -> float:
    return (cx - (box[0] + box[2]) / 2) ** 2 + (cy - (box[1] + box[3]) / 2) ** 2
