from common.geometry_qr import qr_side_px

from calibration.sheet_field import tag_quiet_mm
from calibration.sheet_spec import (
    CELL_PITCHES,
    CONTENT_MM,
    DENSE_CELLS,
    DOT_RATIOS,
    PAGE_H_MM,
    PAGE_W_MM,
    QR_MODULES,
    TAG_COLUMNS,
    TAG_ROWS,
    TAG_SIZES,
    Patch,
)

_GAP = 1.2
_ANCHOR_CELL = 15
_DOT_TAG_MM = 6.0
_FRONT_COLUMNS = 3
_BACK_COLUMNS = 4
_Spec = tuple[str, str, float, float, float, int, float, int]


def front_patches() -> tuple[Patch, ...]:
    x0, y0, width, height = _content()
    codes = _qr_row(x0, y0, width, QR_MODULES)
    top = y0 + max(item.h_mm for item in codes) + _GAP
    specs = _tag_specs() + _cell_specs(CELL_PITCHES, ((11, DOT_RATIOS),))
    return tuple(codes + _grid(x0, top, width, y0 + height - top, _FRONT_COLUMNS, specs, 16))


def back_patches() -> tuple[Patch, ...]:
    x0, y0, width, height = _content()
    cross = ((8, (0.50, 0.62)), (11, DOT_RATIOS))
    return tuple(_grid(x0, y0, width, height, _BACK_COLUMNS, _cell_specs(DENSE_CELLS, cross), 160))


def _content() -> tuple[float, float, float, float]:
    return CONTENT_MM, CONTENT_MM, PAGE_W_MM - 2 * CONTENT_MM, PAGE_H_MM - 2 * CONTENT_MM


def _tag_specs() -> list[_Spec]:
    return [("tag", f"tag-{mm:g}", 0.0, mm, 0.0, _ANCHOR_CELL, 0.62, 5) for mm in TAG_SIZES]


def _cell_specs(cells: tuple[int, ...], cross: tuple[tuple[int, tuple[float, ...]], ...]) -> list[_Spec]:
    specs: list[_Spec] = []
    for cell in cells:
        specs.extend(_dot_spec(cell, ratio) for ratio in DOT_RATIOS)
        specs.extend(_symbol_spec(cell, count, ratio) for count, ratios in cross for ratio in ratios)
    return specs


def _dot_spec(cell: int, ratio: float) -> _Spec:
    return ("dot", f"dot-{cell}-{ratio:g}", 0.0, _DOT_TAG_MM, 0.0, cell, ratio, 5)


def _symbol_spec(cell: int, count: int, ratio: float) -> _Spec:
    return ("symbol", f"sym-{cell}-{count}-{ratio:g}", 0.0, _DOT_TAG_MM, 0.0, cell, ratio, count)


def _grid(x: float, y: float, width: float, height: float, columns: int, specs: list[_Spec], id_start: int) -> list[Patch]:
    rows = len(specs) // columns
    if rows < 1 or rows * columns != len(specs):
        raise ValueError(f"{len(specs)} probes do not fill {columns} columns")
    slot_w, slot_h = width / columns, height / rows
    ids = _Ids(id_start)
    return [
        _patch(spec, x + (index % columns) * slot_w, y + (index // columns) * slot_h, slot_w, slot_h, ids)
        for index, spec in enumerate(specs)
    ]


def _patch(spec: _Spec, x: float, y: float, width: float, height: float, ids: "_Ids") -> Patch:
    kind, name, qr, tag, _pitch_mm, cell, ratio, symbols = spec
    return Patch(kind, name, x, y, width, height, qr, tag, _pitch(width, height, tag), cell, ratio, symbols, ids.take(TAG_COLUMNS * TAG_ROWS))


def _pitch(width: float, height: float, tag: float) -> float:
    quiet = tag_quiet_mm(tag)
    span = tag + 2.0 * quiet
    pitch = min((width - span) / (TAG_COLUMNS - 1), (height - span) / (TAG_ROWS - 1))
    if pitch <= tag:
        raise ValueError(f"slot {width:.1f} x {height:.1f} mm cannot hold a {tag:g} mm tag")
    return pitch


def _qr_row(x: float, y: float, width: float, modules: tuple[float, ...]) -> list[Patch]:
    row: list[Patch] = []
    cursor = x
    for module in modules:
        side = qr_side_px(720, module) * 25.4 / 720.0
        row.append(Patch("qr", f"qr-{module:.2f}", cursor, y, side, side, module, 0.0, 0.0, 0, 0.0, 0, ()))
        cursor += side + _GAP
    if cursor - _GAP > x + width:
        raise ValueError("QR row is wider than the page")
    return row


class _Ids:
    def __init__(self, start: int) -> None:
        self.next_id = start

    def take(self, count: int) -> tuple[int, ...]:
        ids = tuple(range(self.next_id, self.next_id + count))
        self.next_id += count
        return ids
