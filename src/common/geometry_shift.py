from common.geometry_types import TagMark
from common.types import Region

type Box = tuple[int, int, int, int]


def clear_tags(
    slots: tuple[TagMark, ...], block: Region, quiet: int, width: int, height: int, limit: int,
) -> tuple[TagMark, ...]:
    keep = [slot for slot in slots if not touches(tag_box(slot, quiet), _box(block))]
    for slot in slots:
        if not touches(tag_box(slot, quiet), _box(block)):
            continue
        moved = _first_clear(slot, block, quiet, width, height, limit, keep)
        if moved is not None:
            keep.append(moved)
    return tuple(sorted(keep, key=lambda mark: mark.tag_id))


def tag_box(tag: TagMark, quiet: int) -> Box:
    return (tag.x - quiet, tag.y - quiet, tag.size + 2 * quiet, tag.size + 2 * quiet)


def touches(a: Box, b: Box) -> bool:
    return not (a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0] or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1])


def _first_clear(
    slot: TagMark,
    block: Region,
    quiet: int,
    width: int,
    height: int,
    limit: int,
    placed: list[TagMark],
) -> TagMark | None:
    for dx, dy in sorted(_moves(tag_box(slot, quiet), block), key=lambda move: abs(move[0]) + abs(move[1])):
        if abs(dx) + abs(dy) > limit:
            return None
        moved = slot._replace(x=slot.x + dx, y=slot.y + dy)
        box = tag_box(moved, quiet)
        inside = box[0] >= 0 and box[1] >= 0 and box[0] + box[2] <= width and box[1] + box[3] <= height
        if inside and not any(touches(box, tag_box(other, quiet)) for other in placed):
            return moved
    return None


def _moves(box: Box, block: Region) -> list[tuple[int, int]]:
    x, y, w, h = box
    return [
        (block.x - (x + w), 0),
        (block.x + block.width - x, 0),
        (0, block.y - (y + h)),
        (0, block.y + block.height - y),
    ]


def _box(region: Region) -> Box:
    return (region.x, region.y, region.width, region.height)
