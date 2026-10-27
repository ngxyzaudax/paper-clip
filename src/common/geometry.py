from functools import lru_cache

from common.config import PaperClipConfig
from common.format_spec import CALIBRATION_REPEATS
from common.geometry_measure import margin_px, mm_to_px, quantize_mm, snap_down, snap_up
from common.geometry_qr import qr_side_px
from common.geometry_tags import choose_tag_grid, place_tags, tag_pixel_size, tag_quiet_px
from common.geometry_types import PageGeometry, TagMark
from common.types import Region


def page_geometry(config: PaperClipConfig) -> PageGeometry:
    return _page_geometry_cached(_geometry_key(config))


def tag_center_xy(geometry: PageGeometry, tag: TagMark) -> tuple[float, float]:
    return (
        geometry.origin_x + tag.x + tag.size / 2.0,
        geometry.origin_y + tag.y + tag.size / 2.0,
    )


def _geometry_key(config: PaperClipConfig) -> tuple[float | int, ...]:
    return (
        config.num_symbols,
        config.cell_size_px,
        config.print_dpi,
        quantize_mm(config.page_width_mm),
        quantize_mm(config.page_height_mm),
        quantize_mm(config.margin_top_mm),
        quantize_mm(config.margin_right_mm),
        quantize_mm(config.margin_bottom_mm),
        quantize_mm(config.margin_left_mm),
    )


@lru_cache(maxsize=64)
def _page_geometry_cached(key: tuple[float | int, ...]) -> PageGeometry:
    symbols, cell, dpi, page_w_mm, page_h_mm, top, right, bottom, left = key
    page_w = mm_to_px(float(page_w_mm), int(dpi))
    page_h = mm_to_px(float(page_h_mm), int(dpi))
    origin_x = margin_px(float(left), int(dpi), int(cell))
    origin_y = margin_px(float(top), int(dpi), int(cell))
    usable_w = snap_down(page_w - origin_x - margin_px(float(right), int(dpi), int(cell)), int(cell))
    usable_h = snap_down(page_h - origin_y - margin_px(float(bottom), int(dpi), int(cell)), int(cell))
    if usable_w < int(cell) * 4 or usable_h < int(cell) * 4:
        raise ValueError("page margins leave no usable grid")
    qr, calibration, header_h = _header_band(usable_w, int(dpi), int(cell), int(symbols))
    if header_h >= usable_h:
        raise ValueError("header band leaves no data area")
    tag = tag_pixel_size(int(dpi))
    quiet = tag_quiet_px(int(dpi))
    data_h = usable_h - header_h
    tag_rows, tag_cols = choose_tag_grid(usable_w, data_h, tag, quiet, int(dpi))
    tags = place_tags(usable_w, data_h, header_h, tag, quiet, tag_rows, tag_cols)
    forbidden = _forbidden(usable_w, usable_h, header_h, tags, quiet)
    return PageGeometry(
        page_w=page_w,
        page_h=page_h,
        origin_x=origin_x,
        origin_y=origin_y,
        usable_w=usable_w,
        usable_h=usable_h,
        cell=int(cell),
        cols=usable_w // int(cell),
        rows=usable_h // int(cell),
        qr=qr,
        calibration=calibration,
        cal_rows=CALIBRATION_REPEATS,
        header_h=header_h,
        tags=tags,
        tag_rows=tag_rows,
        tag_cols=tag_cols,
        forbidden=forbidden,
    )


def _header_band(usable_w: int, dpi: int, cell: int, num_symbols: int) -> tuple[Region, Region, int]:
    side = qr_side_px(dpi)
    cal_w = num_symbols * cell
    cal_h = CALIBRATION_REPEATS * cell
    gap = cell
    if side > usable_w or cal_w > usable_w:
        raise ValueError("page is too narrow for the QR header and calibration strip")
    if side + gap + cal_w <= usable_w:
        qr = Region(0, 0, side, side)
        calibration = Region(side + gap, 0, cal_w, cal_h)
        band = max(side, cal_h)
    else:
        qr = Region(0, 0, side, side)
        calibration = Region(0, side + gap, cal_w, cal_h)
        band = side + gap + cal_h
    return qr, calibration, snap_up(band, cell)


def _forbidden(
    usable_w: int,
    usable_h: int,
    header_h: int,
    tags: tuple[TagMark, ...],
    quiet: int,
) -> tuple[tuple[int, int, int, int], ...]:
    rects = [(0, 0, usable_w, header_h)]
    for tag in tags:
        rects.append(_expand(tag.x, tag.y, tag.size, tag.size, quiet, usable_w, usable_h))
    return tuple(rects)


def _expand(
    x: int, y: int, width: int, height: int, pad: int, limit_w: int, limit_h: int,
) -> tuple[int, int, int, int]:
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(limit_w, x + width + pad)
    y1 = min(limit_h, y + height + pad)
    return (x0, y0, max(0, x1 - x0), max(0, y1 - y0))
