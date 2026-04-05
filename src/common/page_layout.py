from common.config import PaperClipConfig
from common.layout_metrics import (
    build_config_layout,
    layout_clearance_snapped,
    margin_offset,
    mm_to_px,
    page_image_size,
    qr_region_usable,
    strip_height_px,
    usable_area_px,
)
from common.apriltag_layout import mesh_tag_paste_tuples_for_layout
from common.layout_spatial import center_qr_size_px
from common.page_capacity import (
    data_capacity_bytes,
    data_capacity_symbols,
    grid_dimensions,
    pages_needed,
    valid_cells_ordered,
)
from common.types import Region


def center_qr_target_size_px(config: PaperClipConfig) -> int:
    uw, uh = usable_area_px(config)
    return center_qr_size_px(uw, uh, config.cell_size_px, config.print_dpi)


def data_grid_region(config: PaperClipConfig) -> Region:
    uw, uh = usable_area_px(config)
    cell = config.cell_size_px
    cols = uw // cell
    rows = uh // cell
    return Region(0, 0, cols * cell, rows * cell)


def qr_region(config: PaperClipConfig) -> Region:
    return qr_region_usable(config)


def alignment_tag_placements(config: PaperClipConfig) -> list[tuple[int, int, int, int]]:
    lay = build_config_layout(config)
    clearance = layout_clearance_snapped(config)
    return mesh_tag_paste_tuples_for_layout(lay, config.cell_size_px, clearance)


__all__ = (
    "alignment_tag_placements",
    "center_qr_target_size_px",
    "data_capacity_bytes",
    "data_capacity_symbols",
    "data_grid_region",
    "grid_dimensions",
    "margin_offset",
    "mm_to_px",
    "page_image_size",
    "pages_needed",
    "qr_region",
    "strip_height_px",
    "usable_area_px",
    "valid_cells_ordered",
)
