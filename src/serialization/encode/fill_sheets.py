"""Spend the paper a document already needs on extra robustness.

Unused sides of the last sheet become parity pages and data pages carry as much
Reed-Solomon parity as fits. The priority decides how much of that parity may be
traded for larger cells while the data stays on the same pages.
"""

import math
from dataclasses import dataclass, replace
from typing import Literal

from common.cell_size_picks import CELL_SIZE_PICK_VALUES
from common.config import PaperClipConfig, validate_config
from common.page_layout import data_capacity_bytes, pages_needed
from serialization.encode.fit_ecc import encoded_lengths, largest_ecc
from serialization.encode.frame_payload import interleaved_length

RS_MAX_PAGES = 255
BALANCED_ECC = 128
FillPriority = Literal["protection", "balanced", "dots"]
FILL_PRIORITIES: tuple[FillPriority, ...] = ("protection", "balanced", "dots")


@dataclass(frozen=True)
class SheetPlan:
    sides: int = 1
    fill: bool = False
    sheets: int = 0
    priority: FillPriority = "protection"


def sheets_for(pages: int, sides: int) -> int:
    return max(1, math.ceil(pages / max(1, sides)))


def plan_config(raw: bytes, config: PaperClipConfig, filename: str, plan: SheetPlan) -> PaperClipConfig:
    blob_len, name_len = encoded_lengths(raw, filename)
    filled = _filled(blob_len, name_len, config)
    if not plan.fill:
        return filled
    data_pages = _data_pages(blob_len, name_len, filled)
    slots = _slots(data_pages + config.redundancy_pages, plan)
    floor = _ecc_floor(plan.priority, config.ecc_sym, filled.ecc_sym)
    grown = _grown(blob_len, name_len, replace(filled, ecc_sym=floor), data_pages) or filled
    return _with_parity(grown, slots - _data_pages(blob_len, name_len, grown))


def _ecc_floor(priority: FillPriority, requested: int, filled: int) -> int:
    if priority == "dots":
        return requested
    if priority == "balanced":
        return min(filled, max(requested, BALANCED_ECC))
    return filled


def _filled(blob_len: int, name_len: int, config: PaperClipConfig) -> PaperClipConfig:
    ecc = largest_ecc(blob_len, name_len, config)
    return config if ecc == config.ecc_sym else validate_config(replace(config, ecc_sym=ecc))


def _data_pages(blob_len: int, name_len: int, config: PaperClipConfig) -> int:
    return pages_needed(interleaved_length(blob_len, name_len, config.ecc_sym), config)


def _slots(pages: int, plan: SheetPlan) -> int:
    sides = 2 if plan.sides == 2 else 1
    return min(RS_MAX_PAGES, max(sheets_for(pages, sides), plan.sheets) * sides)


def _with_parity(config: PaperClipConfig, parity: int) -> PaperClipConfig:
    return validate_config(replace(config, redundancy_pages=max(config.redundancy_pages, parity)))


def _grown(blob_len: int, name_len: int, floor: PaperClipConfig, room: int) -> PaperClipConfig | None:
    larger = (cell for cell in reversed(CELL_SIZE_PICK_VALUES) if cell > floor.cell_size_px)
    fitting = (grown for cell in larger if (grown := _at_cell(blob_len, name_len, floor, cell, room)))
    return next(fitting, None)


def _at_cell(
    blob_len: int, name_len: int, floor: PaperClipConfig, cell: int, room: int,
) -> PaperClipConfig | None:
    candidate = _resized(floor, cell)
    if candidate is None or _data_pages(blob_len, name_len, candidate) > room:
        return None
    return _filled(blob_len, name_len, candidate)


def _resized(config: PaperClipConfig, cell: int) -> PaperClipConfig | None:
    try:
        candidate = validate_config(replace(config, cell_size_px=cell))
        return candidate if data_capacity_bytes(candidate) > 0 else None
    except ValueError:
        return None
