from statistics import mean
from typing import NamedTuple

from calibration.sheet_pass import (
    passed_cell,
    passed_dense_pitch,
    passed_pitch,
    passed_qr,
    passed_ratio,
    passed_symbols,
    passed_tag,
)
from calibration.sheet_score import PatchRead
from calibration.sheet_spec import CELL_PITCHES, DENSE_CELLS, DENSE_PITCH_MM, DENSE_QR_MM, DENSE_TAG_MM, DOT_RATIOS, QR_MODULES, TAG_SIZES
from common.config import PaperClipConfig, resolve_config
from common.format_spec import DOT_DIAMETER_RATIO, MIN_CELL_MM, QR_MODULE_MM
from common.page_capacity import data_capacity_bytes

_QR = (*QR_MODULES, *DENSE_QR_MM)
_TAGS = (8.0, *TAG_SIZES, *DENSE_TAG_MM)
_TAG_AXIS = (*TAG_SIZES, *DENSE_TAG_MM)
_PITCH = (16.0, 24.0, 32.0)
_CELLS = (*CELL_PITCHES, *DENSE_CELLS)


class AxisLimit(NamedTuple):
    name: str
    passed: tuple[str, ...]
    failed: tuple[str, ...]
    chosen: str


class ChosenProfile(NamedTuple):
    qr_module_mm: float
    tag_size_mm: float
    tag_pitch_mm: float
    cell_size_px: int
    dot_ratio: float
    num_symbols: int
    bytes_per_side: int


def axis_limits(reads: tuple[PatchRead, ...]) -> tuple[AxisLimit, ...]:
    chosen = choose_profile(reads)
    dense_pitch = passed_dense_pitch(reads)
    return (
        _axis("QR module mm", _QR, passed_qr(reads), chosen.qr_module_mm),
        _axis("AprilTag mm", _TAG_AXIS, passed_tag(reads), chosen.tag_size_mm),
        _axis("Tag pitch mm", _PITCH, passed_pitch(reads), chosen.tag_pitch_mm),
        _axis("Probe 12 mm", DENSE_PITCH_MM, dense_pitch, _probe_mark(dense_pitch)),
        _axis("Cell px", _CELLS, passed_cell(reads), chosen.cell_size_px),
        _axis("Dot ratio", DOT_RATIOS, passed_ratio(reads, chosen.cell_size_px), chosen.dot_ratio),
        _axis("Symbols", (5, 8, 11), passed_symbols(reads, chosen.cell_size_px), chosen.num_symbols),
    )


def choose_profile(reads: tuple[PatchRead, ...]) -> ChosenProfile:
    cell = _legal_cell(reads)
    ratio = _best_ratio(reads, cell)
    symbols = int(_most((5, 8, 11), passed_symbols(reads, cell), 5))
    config = _config(
        float(_safer(_QR, passed_qr(reads), QR_MODULE_MM)),
        float(_safer(_TAGS, passed_tag(reads) | {8.0}, 8.0)),
        float(_safer(_PITCH, passed_pitch(reads), 16.0)),
        cell, ratio, symbols,
    )
    return ChosenProfile(
        config.qr_module_mm, config.tag_size_mm, config.tag_pitch_mm, config.cell_size_px,
        config.dot_ratio, config.num_symbols, data_capacity_bytes(config),
    )


def _legal_cell(reads: tuple[PatchRead, ...]) -> int:
    cell = int(_safer(_CELLS, passed_cell(reads), 22))
    allowed = [item for item in _CELLS if item >= cell and _encodable(item)]
    return allowed[-1] if allowed else 22


def _encodable(cell: int) -> bool:
    return cell * 25.4 / 720.0 >= MIN_CELL_MM


def _probe_mark(passed: set[float]) -> str:
    return "pass" if passed else "fail"


def _config(qr: float, tag: float, pitch: float, cell: int, ratio: float, symbols: int) -> PaperClipConfig:
    return resolve_config(
        cell_size_px=cell, num_symbols=symbols, tag_size_mm=tag, tag_pitch_mm=pitch,
        qr_module_mm=qr, dot_ratio=ratio, print_dpi=720,
    )


def _best_ratio(reads: tuple[PatchRead, ...], cell: int) -> float:
    passed = passed_ratio(reads, cell)
    if not passed:
        return DOT_DIAMETER_RATIO
    return max(passed, key=lambda ratio: (_mean(reads, cell, ratio), ratio == DOT_DIAMETER_RATIO))


def _mean(reads: tuple[PatchRead, ...], cell: int, ratio: float) -> float:
    values = [read.accuracy for read in reads if read.kind == "dot" and read.cell_px == cell and read.dot_ratio == ratio]
    return mean(values) if values else 0.0


def passing_run(ordered: tuple, passed: set) -> int:
    """How many sizes pass in an unbroken run from the safest end of `ordered`."""
    run = 0
    while run < len(ordered) and ordered[run] in passed:
        run += 1
    return run


def _safer(ordered: tuple, passed: set, fallback):
    run = passing_run(ordered, passed)
    if run == 0:
        return fallback
    return ordered[max(0, run - 2)]


def _most(ordered: tuple, passed: set, fallback):
    run = passing_run(ordered, passed)
    return ordered[run - 1] if run else fallback


def _axis(name: str, ordered: tuple, passed: set, chosen) -> AxisLimit:
    return AxisLimit(
        name,
        tuple(str(value) for value in ordered if value in passed),
        tuple(str(value) for value in ordered if value not in passed),
        str(chosen),
    )
