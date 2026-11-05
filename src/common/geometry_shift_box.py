from common.geometry_types import TagMark
from common.types import Region

type Box = tuple[int, int, int, int]


def tag_box(tag: TagMark, quiet: int) -> Box:
    return (tag.x - quiet, tag.y - quiet, tag.size + 2 * quiet, tag.size + 2 * quiet)


def touches(a: Box, b: Box) -> bool:
    return not (a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0] or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1])


def region_box(region: Region) -> Box:
    return (region.x, region.y, region.width, region.height)


def grow_region(region: Region, gap: int) -> Region:
    pad = max(0, gap)
    return Region(region.x - pad, region.y - pad, region.width + 2 * pad, region.height + 2 * pad)
