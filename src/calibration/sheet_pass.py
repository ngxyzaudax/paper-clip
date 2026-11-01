from calibration.sheet_score import PatchRead
from calibration.sheet_spec import (
    CELL_PITCHES,
    DENSE_CELLS,
    DENSE_PITCH_MM,
    DENSE_QR_MM,
    DENSE_TAG_MM,
    DOT_RATIOS,
    QR_MODULES,
    TAG_PITCHES,
    TAG_SIZES,
)

_QR = (*QR_MODULES, *DENSE_QR_MM)
_TAGS = (*TAG_SIZES, *DENSE_TAG_MM)
_CELLS = (*CELL_PITCHES, *DENSE_CELLS)


def passed_qr(reads: tuple[PatchRead, ...]) -> set[float]:
    return {mm for mm in _QR if _all(reads, lambda read, mm=mm: read.kind == "qr" and read.qr_mm == mm, lambda read: read.decoded)}


def passed_tag(reads: tuple[PatchRead, ...]) -> set[float]:
    return {mm for mm in _TAGS if _all(reads, lambda read, mm=mm: read.kind == "tag" and read.tag_mm == mm, _tag_ok)}


def passed_pitch(reads: tuple[PatchRead, ...]) -> set[float]:
    found = {mm for mm in TAG_PITCHES if _all(reads, lambda read: read.kind == "pitch" and read.pitch_mm == mm, dots_ok)}
    if _all(reads, lambda read: read.kind == "dot" and read.cell_px == 22 and read.dot_ratio == 0.62, dots_ok):
        found.add(16.0)
    return found


def passed_cell(reads: tuple[PatchRead, ...]) -> set[int]:
    return {cell for cell in _CELLS if any(pair_ok(reads, cell, ratio) for ratio in DOT_RATIOS)}


def passed_dense_pitch(reads: tuple[PatchRead, ...]) -> set[float]:
    return {mm for mm in DENSE_PITCH_MM if _all(reads, lambda read, mm=mm: read.kind == "pitch" and read.pitch_mm == mm, dots_ok)}


def passed_ratio(reads: tuple[PatchRead, ...], cell: int) -> set[float]:
    return {ratio for ratio in DOT_RATIOS if pair_ok(reads, cell, ratio)}


def passed_symbols(reads: tuple[PatchRead, ...], cell: int) -> set[int]:
    found = {5} if cell in passed_cell(reads) else set()
    for count in (8, 11):
        if _all(reads, lambda read: read.kind == "symbol" and read.cell_px == cell and read.symbols == count, dots_ok):
            found.add(count)
    return found


def pair_ok(reads: tuple[PatchRead, ...], cell: int, ratio: float) -> bool:
    return _all(reads, lambda read: read.kind == "dot" and read.cell_px == cell and read.dot_ratio == ratio, dots_ok)


def dots_ok(read: PatchRead) -> bool:
    return (not read.slipped) and read.accuracy >= 0.99


MAX_TAG_RESIDUAL_CELLS = 0.4


def _tag_ok(read: PatchRead) -> bool:
    rate = read.tags_found / read.tags_expected if read.tags_expected else 0.0
    return rate >= 0.95 and read.residual <= MAX_TAG_RESIDUAL_CELLS and dots_ok(read)


def _all(reads: tuple[PatchRead, ...], pred, ok) -> bool:
    matched = [read for read in reads if pred(read)]
    return bool(matched) and all(ok(read) for read in matched)
