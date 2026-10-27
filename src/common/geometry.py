from functools import lru_cache

from common.config import PaperClipConfig
from common.format_spec import CALIBRATION_REPEATS
from common.geometry_centre import centre_block
from common.geometry_measure import margin_px, mm_to_px, quantize_mm, snap_down
from common.geometry_shift import clear_tags, tag_box
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
        int(round(config.tag_pitch_mm)),
        quantize_mm(config.page_width_mm),
        quantize_mm(config.page_height_mm),
        quantize_mm(config.margin_top_mm),
        quantize_mm(config.margin_right_mm),
        quantize_mm(config.margin_bottom_mm),
        quantize_mm(config.margin_left_mm),
    )


@lru_cache(maxsize=64)
def _page_geometry_cached(key: tuple[float | int, ...]) -> PageGeometry:
    symbols, cell, dpi, pitch_mm, page_w_mm, page_h_mm, top, right, bottom, left = key
    cell, dpi = int(cell), int(dpi)
    page_w = mm_to_px(float(page_w_mm), dpi)
    page_h = mm_to_px(float(page_h_mm), dpi)
    origin_x = margin_px(float(left), dpi, cell)
    origin_y = margin_px(float(top), dpi, cell)
    usable_w = snap_down(page_w - origin_x - margin_px(float(right), dpi, cell), cell)
    usable_h = snap_down(page_h - origin_y - margin_px(float(bottom), dpi, cell), cell)
    if usable_w < cell * 4 or usable_h < cell * 4:
        raise ValueError("page margins leave no usable grid")
    cols, rows = usable_w // cell, usable_h // cell
    centre = centre_block(page_w, page_h, origin_x, origin_y, cols, rows, cell, dpi, int(symbols))
    tag = tag_pixel_size(dpi)
    quiet = tag_quiet_px(dpi)
    tag_rows, tag_cols = choose_tag_grid(usable_w, usable_h, tag, quiet, dpi, float(pitch_mm))
    slots = place_tags(usable_w, usable_h, tag, quiet, tag_rows, tag_cols, cell)
    tags = clear_tags(slots, centre.block, quiet, usable_w, usable_h, _shift_limit(slots, tag_cols))
    if len(tags) < 4:
        raise ValueError("the centred QR header leaves fewer than four alignment tags")
    return PageGeometry(
        page_w=page_w,
        page_h=page_h,
        origin_x=origin_x,
        origin_y=origin_y,
        usable_w=usable_w,
        usable_h=usable_h,
        cell=cell,
        cols=cols,
        rows=rows,
        qr=centre.qr,
        calibration=centre.calibration,
        cal_rows=CALIBRATION_REPEATS,
        centre=centre.block,
        tags=tags,
        tag_rows=tag_rows,
        tag_cols=tag_cols,
        forbidden=_forbidden(usable_w, usable_h, centre.block, tags, quiet),
    )


def _shift_limit(slots: tuple[TagMark, ...], tag_cols: int) -> int:
    across = slots[1].x - slots[0].x if tag_cols > 1 else 0
    down = slots[tag_cols].y - slots[0].y if len(slots) > tag_cols else 0
    pitches = [pitch for pitch in (across, down) if pitch > 0]
    return int(0.75 * min(pitches)) if pitches else 0


def _forbidden(
    usable_w: int,
    usable_h: int,
    centre: Region,
    tags: tuple[TagMark, ...],
    quiet: int,
) -> tuple[tuple[int, int, int, int], ...]:
    rects = [(centre.x, centre.y, centre.width, centre.height)]
    for tag in tags:
        rects.append(_clamp(tag_box(tag, quiet), usable_w, usable_h))
    return tuple(rects)


def _clamp(box: tuple[int, int, int, int], limit_w: int, limit_h: int) -> tuple[int, int, int, int]:
    x, y, width, height = box
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(limit_w, x + width), min(limit_h, y + height)
    return (x0, y0, max(0, x1 - x0), max(0, y1 - y0))
