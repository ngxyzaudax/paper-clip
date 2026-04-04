from common.config import PaperClipConfig
from common.layout_metrics import (
    build_config_layout,
    finder_pattern_size,
    layout_clearance_snapped,
    margin_offset,
    mm_to_px,
    page_image_size,
    qr_region_usable,
    strip_height_px,
    usable_area_px,
)
from common.layout_spatial import (
    center_qr_size_px,
    corner_tag_centers,
    flank_tag_centers,
    tag_paste_top_left,
)
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
    return center_qr_size_px(uw, uh, config.cell_size_px)


def data_grid_region(config: PaperClipConfig) -> Region:
    uw, uh = usable_area_px(config)
    cell = config.cell_size_px
    cols = uw // cell
    rows = uh // cell
    return Region(0, 0, cols * cell, rows * cell)


def qr_region(config: PaperClipConfig) -> Region:
    return qr_region_usable(config)


def alignment_tag_placements(config: PaperClipConfig) -> list[tuple[int, int, int, int]]:
    from common.apriltag_markers import (
        BR_TAG_ID,
        FLANK_TAG_IDS,
        BL_TAG_ID,
        TL_TAG_ID,
        TR_TAG_ID,
    )

    uw, uh = usable_area_px(config)
    cell = config.cell_size_px
    fp = finder_pattern_size(config)
    lay = build_config_layout(config)
    clearance = layout_clearance_snapped(config)
    corner_ids = (TL_TAG_ID, TR_TAG_ID, BL_TAG_ID, BR_TAG_ID)
    out: list[tuple[int, int, int, int]] = []
    for i, (tcx, tcy) in enumerate(corner_tag_centers(uw, uh, fp, clearance)):
        lx, ty = tag_paste_top_left(tcx, tcy, fp, cell)
        out.append((lx, ty, corner_ids[i], fp))
    for i, (tcx, tcy) in enumerate(flank_tag_centers(lay, clearance)):
        lx, ty = tag_paste_top_left(tcx, tcy, fp, cell)
        out.append((lx, ty, FLANK_TAG_IDS[i], fp))
    return out


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
