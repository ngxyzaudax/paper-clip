from common.geometry_shift_box import region_box, tag_box, touches
from common.geometry_types import TagMark
from common.types import Region

type Box = tuple[int, int, int, int]


def park_tag(
    slot: TagMark,
    guarded: tuple[Region, ...],
    blocks: tuple[Region, ...],
    quiet: int,
    width: int,
    height: int,
    limit: int,
    placed: list[TagMark],
    gap: int,
) -> TagMark | None:
    moved = _first_clear(slot, guarded, quiet, width, height, limit, placed)
    if moved is not None:
        return moved
    return _within_limit(slot, blocks, quiet, width, height, limit, placed, gap)


def _first_clear(
    slot: TagMark,
    blocks: tuple[Region, ...],
    quiet: int,
    width: int,
    height: int,
    limit: int,
    placed: list[TagMark],
) -> TagMark | None:
    moves = _ordered(slot, blocks, quiet)
    for dx, dy in moves:
        if abs(dx) + abs(dy) > limit:
            return None
        moved = _accepted(slot, dx, dy, blocks, quiet, width, height, placed)
        if moved is not None:
            return moved
    return None


def _within_limit(
    slot: TagMark,
    blocks: tuple[Region, ...],
    quiet: int,
    width: int,
    height: int,
    limit: int,
    placed: list[TagMark],
    gap: int,
) -> TagMark | None:
    for dx, dy in _ordered(slot, blocks, quiet):
        moved = _longest(slot, dx, dy, gap, blocks, quiet, width, height, limit, placed)
        if moved is not None:
            return moved
    return None


def _longest(
    slot: TagMark,
    dx: int,
    dy: int,
    gap: int,
    blocks: tuple[Region, ...],
    quiet: int,
    width: int,
    height: int,
    limit: int,
    placed: list[TagMark],
) -> TagMark | None:
    for extra in range(max(0, gap), -1, -1):
        ndx, ndy = _extend(dx, dy, extra)
        if abs(ndx) + abs(ndy) > limit:
            continue
        moved = _accepted(slot, ndx, ndy, blocks, quiet, width, height, placed)
        if moved is not None:
            return moved
    return None


def _ordered(slot: TagMark, blocks: tuple[Region, ...], quiet: int) -> list[tuple[int, int]]:
    return sorted(set(_clearing_moves(slot, blocks, quiet)), key=lambda move: abs(move[0]) + abs(move[1]))


def _extend(dx: int, dy: int, extra: int) -> tuple[int, int]:
    if dx > 0:
        return dx + extra, dy
    if dx < 0:
        return dx - extra, dy
    if dy > 0:
        return dx, dy + extra
    if dy < 0:
        return dx, dy - extra
    return dx, dy


def _accepted(
    slot: TagMark,
    dx: int,
    dy: int,
    blocks: tuple[Region, ...],
    quiet: int,
    width: int,
    height: int,
    placed: list[TagMark],
) -> TagMark | None:
    moved = slot._replace(x=slot.x + dx, y=slot.y + dy)
    box = tag_box(moved, quiet)
    inside = box[0] >= 0 and box[1] >= 0 and box[0] + box[2] <= width and box[1] + box[3] <= height
    blocked = any(touches(box, region_box(block)) for block in blocks)
    crowded = any(touches(box, tag_box(other, quiet)) for other in placed)
    if inside and not blocked and not crowded:
        return moved
    return None


def _clearing_moves(slot: TagMark, blocks: tuple[Region, ...], quiet: int) -> list[tuple[int, int]]:
    box = tag_box(slot, quiet)
    moves: list[tuple[int, int]] = []
    for block in blocks:
        if touches(box, region_box(block)):
            moves.extend(_moves(box, block))
    return moves


def _moves(box: Box, block: Region) -> list[tuple[int, int]]:
    x, y, width, height = box
    return [
        (block.x - (x + width), 0),
        (block.x + block.width - x, 0),
        (0, block.y - (y + height)),
        (0, block.y + block.height - y),
    ]
