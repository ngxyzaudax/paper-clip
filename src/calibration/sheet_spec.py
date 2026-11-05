from typing import NamedTuple

QR_MODULES = (0.25, 0.22, 0.20)
TAG_SIZES = (8.0, 6.0, 5.0)
TAG_PITCHES = ()
CELL_PITCHES = (15, 14, 13)
DOT_RATIOS = (0.50, 0.62, 0.75)
SYMBOL_COUNTS = (8, 11)
DENSE_QR_MM = ()
DENSE_TAG_MM = ()
DENSE_CELLS = (12, 11, 10, 9, 8)
QR_MODULE_COUNT = 65
TAG_COLUMNS = 3
TAG_ROWS = 2
FRAME_TAG_MM = 8.0
PAGE_W_MM = 210.0
PAGE_H_MM = 297.0
CONTENT_MM = 14.8


class FrameTag(NamedTuple):
    tag_id: int
    x_mm: float
    y_mm: float


class Patch(NamedTuple):
    kind: str
    name: str
    x_mm: float
    y_mm: float
    w_mm: float
    h_mm: float
    qr_mm: float
    tag_mm: float
    pitch_mm: float
    cell_px: int
    dot_ratio: float
    symbols: int
    tag_ids: tuple[int, ...]


class SheetSide(NamedTuple):
    name: str
    frame: tuple[FrameTag, ...]
    patches: tuple[Patch, ...]
