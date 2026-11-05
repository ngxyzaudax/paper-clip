from statistics import mean
from typing import NamedTuple

from calibration.sheet_cell import safe_cell
from calibration.sheet_pass import (
    passed_cell,
    passed_pitch,
    passed_qr,
    passed_ratio,
    passed_symbols,
    passed_tag,
)
from calibration.sheet_score import PatchRead
from calibration.sheet_spec import CELL_PITCHES, DENSE_CELLS, DENSE_QR_MM, DENSE_TAG_MM, DOT_RATIOS, QR_MODULES, TAG_SIZES
from common.config import PaperClipConfig, resolve_config
from common.format_spec import DOT_DIAMETER_RATIO, MIN_CELL_MM, QR_MODULE_MM
from common.page_capacity import data_capacity_bytes

_QR = (*QR_MODULES, *DENSE_QR_MM)
_TAGS = tuple(dict.fromkeys((8.0, *TAG_SIZES, *DENSE_TAG_MM)))
_PITCH = (16.0,)
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
    return (
        _axis("QR module mm", _QR, passed_qr(reads), chosen.qr_module_mm),
        _axis("AprilTag mm", _TAGS, passed_tag(reads), chosen.tag_size_mm),
        _axis("Tag pitch mm", _PITCH, passed_pitch(reads) | {16.0}, chosen.tag_pitch_mm),
        _axis("Cell px", _CELLS, passed_cell(reads), chosen.cell_size_px),
        _axis("Dot ratio", DOT_RATIOS, passed_ratio(reads, chosen.cell_size_px), chosen.dot_ratio),
        _axis("Symbols", (5, 8, 11), passed_symbols(reads, chosen.cell_size_px), chosen.num_symbols),
    )


def choose_profile(reads: tuple[PatchRead, ...]) -> ChosenProfile:
    cell, symbols = _densest(reads)
    ratio = _best_ratio(reads, cell)
    config = _config(
        float(_safer(_QR, passed_qr(reads), QR_MODULE_MM)),
        float(_safer(_TAGS, passed_tag(reads), 8.0)),
        float(_safer(_PITCH, passed_pitch(reads) | {16.0}, 16.0)),
        cell, ratio, symbols,
    )
    return ChosenProfile(
        config.qr_module_mm, config.tag_size_mm, config.tag_pitch_mm, config.cell_size_px,
        config.dot_ratio, config.num_symbols, data_capacity_bytes(config),
    )


def _densest(reads: tuple[PatchRead, ...]) -> tuple[int, int]:
    return safe_cell(reads, _CELLS)


def _encodable(cell: int) -> bool:
    return cell * 25.4 / 720.0 >= MIN_CELL_MM


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


def passing_run[T](ordered: tuple[T, ...], passed: set[T]) -> int:
    """How many sizes pass in an unbroken run from the safest end of `ordered`."""
    run = 0
    while run < len(ordered) and ordered[run] in passed:
        run += 1
    return run


def _safer[T](ordered: tuple[T, ...], passed: set[T], fallback: T) -> T:
    run = passing_run(ordered, passed)
    if run == 0:
        return fallback
    return ordered[max(0, run - 2)]


def _axis[T](name: str, ordered: tuple[T, ...], passed: set[T], chosen: T) -> AxisLimit:
    return AxisLimit(
        name,
        tuple(str(value) for value in ordered if value in passed),
        tuple(str(value) for value in ordered if value not in passed),
        str(chosen),
    )
