from common.geometry_qr import qr_side_px

from calibration.sheet_spec import (
    CELL_PITCHES,
    CONTENT_MM,
    DOT_RATIOS,
    DOT_TAG_MM,
    DOT_TAG_PITCH_MM,
    FRAME_TAG_MM,
    PAGE_H_MM,
    PAGE_W_MM,
    QR_MODULES,
    SAFE_PITCH_MM,
    SAFE_TAG_MM,
    SYMBOL_CELLS,
    SYMBOL_COUNTS,
    TAG_COLUMNS,
    TAG_PITCHES,
    TAG_ROWS,
    TAG_SIZES,
    FrameTag,
    Patch,
    SheetSide,
)

_GAP = 1.2


def sheet_side(name: str) -> SheetSide:
    x0, y0, width, height = CONTENT_MM, CONTENT_MM, PAGE_W_MM - 2 * CONTENT_MM, PAGE_H_MM - 2 * CONTENT_MM
    if name == "back":
        from calibration.sheet_back import back_patches

        return SheetSide(name, _frame(name), back_patches(x0, y0, width, height))
    cursor = y0
    patches: list[Patch] = []
    ids = _Ids(100)
    cursor = _add(patches, _qr_row(x0, cursor, width), cursor, _GAP)
    cursor = _add(patches, _grid(x0, cursor, width, 3, 28.0, _tag_specs(), ids), cursor, _GAP)
    cursor = _add(patches, _grid(x0, cursor, width, 2, 44.0, _pitch_specs(), ids), cursor, _GAP)
    cursor = _add(patches, _grid(x0, cursor, width, 4, 27.0, _dot_specs(), ids), cursor, _GAP)
    cursor = _add(patches, _grid(x0, cursor, width, 3, 27.0, _symbol_specs(), ids), cursor, _GAP)
    if cursor > y0 + height:
        raise ValueError(f"{name} patches end at {cursor:.1f} mm, past {y0 + height:.1f}")
    return SheetSide(name, _frame(name), tuple(patches))


def _add(patches: list[Patch], band: list[Patch], cursor: float, gap: float) -> float:
    patches.extend(band)
    if not band:
        return cursor
    return max(item.y_mm + item.h_mm for item in band) + gap


class _Ids:
    def __init__(self, start: int) -> None:
        self.next_id = start

    def take(self, count: int) -> tuple[int, ...]:
        ids = tuple(range(self.next_id, self.next_id + count))
        self.next_id += count
        return ids


def _qr_row(x0: float, y0: float, width: float) -> list[Patch]:
    x = x0
    row: list[Patch] = []
    for module in QR_MODULES:
        side = qr_side_px(720, module) * 25.4 / 720.0
        if x + side > x0 + width + 0.1:
            raise ValueError("QR row does not fit")
        row.append(Patch("qr", f"qr-{module:.2f}", x, y0, side, side, module, 0, 0, 0, 0, 0, ()))
        x += side + _GAP
    return row


def _grid(
    x0: float, y0: float, width: float, columns: int, slot_h: float, specs: list[tuple], ids: _Ids,
) -> list[Patch]:
    slot_w = width / columns
    row: list[Patch] = []
    for index, spec in enumerate(specs):
        column, line = index % columns, index // columns
        row.append(_patch(spec, x0 + column * slot_w, y0 + line * slot_h, slot_w - 0.8, slot_h - 0.8, ids))
    return row


def _patch(spec: tuple, x: float, y: float, w: float, h: float, ids: _Ids) -> Patch:
    kind, name, qr, tag, pitch, cell, ratio, symbols = spec
    tag_ids = () if kind == "qr" else ids.take(TAG_COLUMNS * TAG_ROWS)
    return Patch(kind, name, x, y, w, h, qr, tag, pitch, cell, ratio, symbols, tag_ids)


def _tag_specs() -> list[tuple]:
    return [("tag", f"tag-{mm:g}", 0, mm, SAFE_PITCH_MM, 26, 0.62, 5) for mm in TAG_SIZES]


def _pitch_specs() -> list[tuple]:
    return [("pitch", f"pitch-{mm:g}", 0, SAFE_TAG_MM, mm, 26, 0.62, 5) for mm in TAG_PITCHES]


def _dot_specs() -> list[tuple]:
    return [
        ("dot", f"dot-{cell}-{ratio:g}", 0, DOT_TAG_MM, DOT_TAG_PITCH_MM, cell, ratio, 5)
        for cell in CELL_PITCHES for ratio in DOT_RATIOS
    ]


def _symbol_specs() -> list[tuple]:
    return [
        ("symbol", f"sym-{cell}-{count}", 0, DOT_TAG_MM, DOT_TAG_PITCH_MM, cell, 0.62, count)
        for cell in SYMBOL_CELLS for count in SYMBOL_COUNTS
    ]


def _frame(side: str) -> tuple[FrameTag, ...]:
    base = 500 if side == "front" else 520
    points = [(x, 9.0) for x in (9.0, 60.0, 111.0, 162.0, 201.0)]
    points += [(x, PAGE_H_MM - 9.0) for x in (9.0, 60.0, 111.0, 162.0, 201.0)]
    points += [(9.0, y) for y in (80.0, 151.0, 222.0)]
    points += [(PAGE_W_MM - 9.0, y) for y in (80.0, 151.0, 222.0)]
    if any(abs(x) < FRAME_TAG_MM for x, _y in points):
        raise ValueError("frame tag leaves the page")
    return tuple(FrameTag(base + index, x, y) for index, (x, y) in enumerate(points))
