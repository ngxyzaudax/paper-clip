from typing import NamedTuple

from common.types import Region


class TagMark(NamedTuple):
    tag_id: int
    row: int
    col: int
    x: int
    y: int
    size: int


class PageGeometry(NamedTuple):
    page_w: int
    page_h: int
    origin_x: int
    origin_y: int
    usable_w: int
    usable_h: int
    cell: int
    cols: int
    rows: int
    qr: Region
    calibration: Region
    cal_rows: int
    centre: Region
    tags: tuple[TagMark, ...]
    tag_rows: int
    tag_cols: int
    forbidden: tuple[tuple[int, int, int, int], ...]
