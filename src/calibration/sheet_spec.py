from typing import NamedTuple

QR_MODULES = (0.36, 0.33, 0.30, 0.27, 0.25, 0.22, 0.20)
TAG_SIZES = (6.0, 5.0, 4.0, 3.5, 3.0, 2.5)
TAG_PITCHES = (24.0, 32.0)
CELL_PITCHES = (22, 20, 18, 17)
DOT_RATIOS = (0.50, 0.62, 0.75)
SYMBOL_CELLS = (22, 20, 18)
SYMBOL_COUNTS = (8, 11)
DENSE_QR_MM = (0.18,)
DENSE_TAG_MM = (2.0,)
DENSE_PITCH_MM = (12.0,)
DENSE_CELLS = (16, 15, 14, 13)
SYMBOL_PROBE_CELLS = (17, *DENSE_CELLS)
QR_MODULE_COUNT = 65
SAFE_TAG_MM = 8.0
DOT_TAG_MM = 6.0
SAFE_PITCH_MM = 16.0
DOT_TAG_PITCH_MM = 16.0
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
