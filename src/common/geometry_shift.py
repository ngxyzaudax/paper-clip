from common.geometry_shift_box import grow_region, region_box, tag_box, touches
from common.geometry_shift_limit import park_tag
from common.geometry_types import TagMark
from common.types import Region

__all__ = ["clear_tags", "tag_box", "touches"]


def clear_tags(
    slots: tuple[TagMark, ...],
    blocks: tuple[Region, ...],
    quiet: int,
    width: int,
    height: int,
    limit: int,
    gap: int = 0,
) -> tuple[TagMark, ...]:
    guarded = tuple(grow_region(block, gap) for block in blocks)
    keep = [slot for slot in slots if not _hits(slot, blocks, quiet)]
    for slot in slots:
        if not _hits(slot, blocks, quiet):
            continue
        moved = park_tag(slot, guarded, blocks, quiet, width, height, limit, keep, gap)
        if moved is not None:
            keep.append(moved)
    return tuple(sorted(keep, key=lambda mark: mark.tag_id))


def _hits(slot: TagMark, blocks: tuple[Region, ...], quiet: int) -> bool:
    box = tag_box(slot, quiet)
    return any(touches(box, region_box(block)) for block in blocks)
