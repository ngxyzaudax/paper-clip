from common.geometry_qr import qr_side_px

from calibration.sheet_place import _GAP, _Ids, _add, _grid
from calibration.sheet_spec import (
    DENSE_CELLS,
    DENSE_PITCH_MM,
    DENSE_QR_MM,
    DENSE_TAG_MM,
    DOT_RATIOS,
    DOT_TAG_MM,
    DOT_TAG_PITCH_MM,
    SAFE_PITCH_MM,
    SYMBOL_COUNTS,
    SYMBOL_PROBE_CELLS,
    Patch,
)

_OPEN_H = 26.0
_ROW_H = 27.0


def back_patches(x0: float, y0: float, width: float, height: float) -> tuple[Patch, ...]:
    """Finer probes that use the second face: smaller QR, tags, pitch, and cells."""
    patches: list[Patch] = []
    ids = _Ids(300)
    cursor = _opening(patches, ids, x0, y0, width)
    cursor = _add(patches, _grid(x0, cursor, width, 4, _ROW_H, _dot_specs(), ids), cursor, _GAP)
    cursor = _add(patches, _grid(x0, cursor, width, 4, _ROW_H, _symbol_specs(), ids), cursor, _GAP)
    if cursor > y0 + height:
        raise ValueError(f"back patches end at {cursor:.1f} mm, past {y0 + height:.1f}")
    return tuple(patches)


def _opening(patches: list[Patch], ids: _Ids, x0: float, y0: float, width: float) -> float:
    qr = _qr(x0, y0, DENSE_QR_MM[0])
    band_x = x0 + qr.w_mm + _GAP
    band = _grid(band_x, y0, width - (band_x - x0), 2, _OPEN_H, _opening_specs(), ids)
    return _add(patches, [qr, *band], y0, _GAP)


def _qr(x: float, y: float, module: float) -> Patch:
    side = qr_side_px(720, module) * 25.4 / 720.0
    return Patch("qr", f"qr-{module:.2f}", x, y, side, side, module, 0.0, 0.0, 0, 0.0, 0, ())


def _opening_specs() -> list[tuple]:
    tag = DENSE_TAG_MM[0]
    pitch = DENSE_PITCH_MM[0]
    return [
        ("tag", f"tag-{tag:g}", 0, tag, SAFE_PITCH_MM, 26, 0.62, 5),
        ("pitch", f"pitch-{pitch:g}", 0, DOT_TAG_MM, pitch, 16, 0.62, 5),
    ]


def _dot_specs() -> list[tuple]:
    return [
        ("dot", f"dot-{cell}-{ratio:g}", 0, DOT_TAG_MM, DOT_TAG_PITCH_MM, cell, ratio, 5)
        for cell in DENSE_CELLS for ratio in DOT_RATIOS
    ]


def _symbol_specs() -> list[tuple]:
    return [
        ("symbol", f"sym-{cell}-{count}", 0, DOT_TAG_MM, DOT_TAG_PITCH_MM, cell, 0.62, count)
        for cell in SYMBOL_PROBE_CELLS for count in SYMBOL_COUNTS
    ]
