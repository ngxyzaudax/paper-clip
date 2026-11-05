from typing import NamedTuple

import numpy as np

from health.header_note import header_summary
from health.pages import PageHealth, page_damage
from serialization.decode.assemble_slots import Assembly
from serialization.decode.repair import BlockRepair
from serialization.encode.qr_header import DecodedQrHeader

REBUILT_WITH_SPARE_CAP = 35.0
REBUILT_WITHOUT_SPARE_CAP = 15.0
RECOVERED_FLOOR = 0.1


class HealthReport(NamedTuple):
    health: float
    average: float
    blocks: int
    ecc_sym: int
    repaired_bytes: int
    damaged_bytes: int
    payload_bytes: int
    pages: tuple[PageHealth, ...]
    missing_pages: tuple[int, ...]
    spare_pages: int
    lost: bool
    header_note: str = ""


def block_margin(block: BlockRepair, ecc_sym: int) -> float:
    """Share of a block's repair budget still unused: errors cost two parity bytes, erasures one."""
    return max(0.0, 1.0 - (2 * block.errors + block.erasures) / ecc_sym)


def measure_health(assembly: Assembly, wrong: tuple[np.ndarray, ...]) -> HealthReport:
    repair = assembly.repair
    margins = [block_margin(block, repair.ecc_sym) for block in repair.blocks] or [0.0]
    header = assembly.header
    spare = _spare(assembly.scanned, assembly.rebuilt, header.data_pages)
    return HealthReport(
        health=_overall(100.0 * min(margins), assembly.rebuilt, spare),
        average=round(100.0 * sum(margins) / len(margins), 1),
        blocks=len(repair.blocks),
        ecc_sym=repair.ecc_sym,
        repaired_bytes=len(repair.repaired),
        damaged_bytes=len(repair.damaged),
        payload_bytes=header.payload_length,
        pages=page_damage(assembly, wrong),
        missing_pages=_missing(assembly.scanned, header.total_pages),
        spare_pages=spare,
        lost=False,
        header_note=header_summary(assembly.observed),
    )


def lost_health(
    header: DecodedQrHeader, scanned: tuple[int, ...], header_note: str = "",
) -> HealthReport:
    return HealthReport(
        health=0.0,
        average=0.0,
        blocks=0,
        ecc_sym=header.ecc_sym,
        repaired_bytes=0,
        damaged_bytes=0,
        payload_bytes=header.payload_length,
        pages=(),
        missing_pages=_missing(scanned, header.total_pages),
        spare_pages=0,
        lost=True,
        header_note=header_note,
    )


def _overall(block_health: float, rebuilt: tuple[int, ...], spare: int) -> float:
    """Recovered files never read 0%, and a page rebuilt from page parity caps health."""
    cap = 100.0 if not rebuilt else REBUILT_WITH_SPARE_CAP if spare else REBUILT_WITHOUT_SPARE_CAP
    return round(max(RECOVERED_FLOOR, min(block_health, cap)), 1)


def _missing(scanned: tuple[int, ...], total_pages: int) -> tuple[int, ...]:
    return tuple(index for index in range(total_pages) if index not in scanned)


def _spare(scanned: tuple[int, ...], rebuilt: tuple[int, ...], data_pages: int) -> int:
    return max(0, sum(index >= data_pages for index in scanned) - len(rebuilt))
