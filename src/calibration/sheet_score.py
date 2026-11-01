from typing import NamedTuple

import numpy as np

from calibration.sheet_align import frame_matrix, leave_one_out, warp_patch, warp_qr
from calibration.sheet_orient import page_rotation
from calibration.sheet_place import sheet_side
from calibration.sheet_sample import dot_accuracy
from calibration.sheet_spec import Patch, SheetSide
from common.qr_scale import qr_mm_from_flags
from serialization.decode.detect_tags import detect_tags
from serialization.decode.errors import DecodeError
from serialization.decode.read_qr import read_qr_header


class PatchRead(NamedTuple):
    kind: str
    name: str
    qr_mm: float
    tag_mm: float
    pitch_mm: float
    cell_px: int
    dot_ratio: float
    symbols: int
    decoded: bool
    tags_found: int
    tags_expected: int
    residual: float
    slipped: bool
    accuracy: float


class ScanRead(NamedTuple):
    side: str
    rotation: int
    reads: tuple[PatchRead, ...]


def score_page(image: np.ndarray) -> tuple[str, tuple[PatchRead, ...]]:
    found = read_scan(image)
    return found.side, found.reads


def read_scan(image: np.ndarray) -> ScanRead:
    side = _side_for(image)
    if side is None:
        return ScanRead("", 0, ())
    found = _locate(image, side)
    matrix = frame_matrix(side, found)
    if matrix is None:
        return ScanRead(side.name, 0, ())
    reads = tuple(_score_patch(image, patch, found, matrix) for patch in side.patches)
    return ScanRead(side.name, page_rotation(matrix), reads)


def _side_for(image: np.ndarray) -> SheetSide | None:
    found = detect_tags(image, set(range(500, 516)) | set(range(520, 536)))
    front, back = sheet_side("front"), sheet_side("back")
    front_hits = sum(tag.tag_id in found for tag in front.frame)
    back_hits = sum(tag.tag_id in found for tag in back.frame)
    if max(front_hits, back_hits) < 4:
        return None
    return front if front_hits >= back_hits else back


def _locate(image: np.ndarray, side: SheetSide) -> dict[int, np.ndarray]:
    ids = {tag.tag_id for tag in side.frame}
    ids.update(tag_id for patch in side.patches for tag_id in patch.tag_ids)
    return detect_tags(image, ids)


def _score_patch(image: np.ndarray, patch: Patch, found: dict[int, np.ndarray], matrix: np.ndarray) -> PatchRead:
    if patch.kind == "qr":
        return _qr_read(image, patch, matrix)
    present = sum(tag_id in found for tag_id in patch.tag_ids)
    warped = warp_patch(image, patch, found)
    accuracy, slipped = (0.0, True) if warped is None else dot_accuracy(warped, patch)
    return _read(patch, False, present, len(patch.tag_ids), leave_one_out(patch, found), slipped, accuracy)


def _qr_read(image: np.ndarray, patch: Patch, matrix: np.ndarray) -> PatchRead:
    decoded = _qr_matches(warp_qr(image, patch, matrix), patch.qr_mm)
    return _read(patch, decoded, 0, 0, 0.0, False, 1.0 if decoded else 0.0)


def _qr_matches(crop: np.ndarray, module_mm: float) -> bool:
    try:
        _page, header, _points = read_qr_header(crop)
    except DecodeError:
        return False
    return abs(qr_mm_from_flags(header.flags) - module_mm) <= 0.005


def _read(patch: Patch, decoded: bool, found: int, expected: int, residual: float, slipped: bool, accuracy: float) -> PatchRead:
    return PatchRead(
        patch.kind, patch.name, patch.qr_mm, patch.tag_mm, patch.pitch_mm, patch.cell_px,
        patch.dot_ratio, patch.symbols, decoded, found, expected, residual, slipped, accuracy,
    )
