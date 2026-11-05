from bisect import bisect_right
from itertools import accumulate
from typing import NamedTuple

import numpy as np

from health.damage_map import DamageMap, empty_map, page_damage_map
from serialization.decode.assemble_slots import Assembly


class PageHealth(NamedTuple):
    index: int
    damaged: int
    size: int
    rebuilt: bool
    damage_map: DamageMap


def page_damage(assembly: Assembly, wrong: tuple[np.ndarray, ...]) -> tuple[PageHealth, ...]:
    """Wrong bytes per data page, with the misread cells of each scanned page located on a coarse zone map."""
    local = local_positions(assembly.repair.damaged, assembly.page_sizes)
    maps = {
        page.header.page_index: page_damage_map(cells, page.header)
        for page, cells in zip(assembly.observed, wrong)
    }
    return tuple(
        PageHealth(index, len(local[index]), size, index in assembly.rebuilt, maps.get(index, empty_map()))
        for index, size in enumerate(assembly.page_sizes)
    )


def local_positions(positions: tuple[int, ...], page_sizes: tuple[int, ...]) -> list[list[int]]:
    """Stream positions split per data page and made relative to the start of that page."""
    bounds = list(accumulate(page_sizes))
    starts = [0, *bounds[:-1]]
    local: list[list[int]] = [[] for _ in page_sizes]
    for position in positions:
        page = bisect_right(bounds, position)
        if page < len(local):
            local[page].append(position - starts[page])
    return local
