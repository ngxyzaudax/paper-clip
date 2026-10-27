from common.config import PaperClipConfig
from common.legacy_layout import APRILTAG_EDGE_CELLS, FIDUCIAL_DPI, layout_clearance_px
from common.layout_spatial import (
    UsableLayout,
    build_usable_layout,
    fiducial_px_to_print_px,
    forbidden_rects_usable,
    print_px_to_fiducial_px,
)
from common.types import Region


def mm_to_px(mm: float, dpi: int) -> int:
    return int(mm * dpi / 25.4)


def snap_margin_px(px: int, cell: int) -> int:
    return ((px + cell // 2) // cell) * cell


def usable_area_px(config: PaperClipConfig) -> tuple[int, int]:
    cell = config.cell_size_px
    total_w = mm_to_px(config.page_width_mm, config.print_dpi)
    total_h = mm_to_px(config.page_height_mm, config.print_dpi)
    ml = snap_margin_px(mm_to_px(config.margin_left_mm, config.print_dpi), cell)
    mr = snap_margin_px(mm_to_px(config.margin_right_mm, config.print_dpi), cell)
    mt = snap_margin_px(mm_to_px(config.margin_top_mm, config.print_dpi), cell)
    mb = snap_margin_px(mm_to_px(config.margin_bottom_mm, config.print_dpi), cell)
    uw = total_w - ml - mr
    uh = total_h - mt - mb
    uw = max(cell, (uw // cell) * cell)
    uh = max(cell, (uh // cell) * cell)
    return uw, uh


def layout_clearance_snapped(config: PaperClipConfig) -> int:
    cell = config.cell_size_px
    r = layout_clearance_px(config.print_dpi)
    return max(cell, (r // cell) * cell)


def finder_pattern_size(config: PaperClipConfig) -> int:
    c = config.cell_size_px
    d = config.print_dpi
    cell_f = max(1, print_px_to_fiducial_px(c, d, FIDUCIAL_DPI))
    fp_f = APRILTAG_EDGE_CELLS * cell_f
    return fiducial_px_to_print_px(fp_f, d, FIDUCIAL_DPI)


def strip_height_px(config: PaperClipConfig) -> int:
    return 0


def build_config_layout(config: PaperClipConfig) -> UsableLayout:
    uw, uh = usable_area_px(config)
    return build_usable_layout(
        uw,
        uh,
        config.cell_size_px,
        finder_pattern_size(config),
        strip_height_px(config),
        config.print_dpi,
    )


def layout_forbidden_rects(config: PaperClipConfig) -> list[tuple[int, int, int, int]]:
    return forbidden_rects_usable(
        build_config_layout(config), layout_clearance_snapped(config),
    )


def page_image_size(config: PaperClipConfig) -> tuple[int, int]:
    width = mm_to_px(config.page_width_mm, config.print_dpi)
    height = mm_to_px(config.page_height_mm, config.print_dpi)
    return width, height


def margin_offset(config: PaperClipConfig) -> tuple[int, int]:
    cell = config.cell_size_px
    ml = snap_margin_px(mm_to_px(config.margin_left_mm, config.print_dpi), cell)
    mt = snap_margin_px(mm_to_px(config.margin_top_mm, config.print_dpi), cell)
    return ml, mt


def qr_region_usable(config: PaperClipConfig) -> Region:
    lay = build_config_layout(config)
    return Region(lay.qx, lay.qy, lay.qr_s, lay.qr_s)
