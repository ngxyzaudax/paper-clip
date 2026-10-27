from common.config import PaperClipConfig
from common.geometry import page_geometry
from common.geometry_measure import mm_to_px
from common.page_capacity import (
    data_capacity_bytes,
    data_capacity_symbols,
    grid_dimensions,
    pages_needed,
    valid_cells_ordered,
)
from common.types import Region


def page_image_size(config: PaperClipConfig) -> tuple[int, int]:
    geometry = page_geometry(config)
    return geometry.page_w, geometry.page_h


def margin_offset(config: PaperClipConfig) -> tuple[int, int]:
    geometry = page_geometry(config)
    return geometry.origin_x, geometry.origin_y


def usable_area_px(config: PaperClipConfig) -> tuple[int, int]:
    geometry = page_geometry(config)
    return geometry.usable_w, geometry.usable_h


def data_grid_region(config: PaperClipConfig) -> Region:
    geometry = page_geometry(config)
    return Region(0, 0, geometry.cols * geometry.cell, geometry.rows * geometry.cell)


def qr_region(config: PaperClipConfig) -> Region:
    return page_geometry(config).qr


def strip_height_px(config: PaperClipConfig) -> int:
    return page_geometry(config).header_h


def alignment_tag_placements(config: PaperClipConfig) -> list[tuple[int, int, int, int]]:
    return [(tag.x, tag.y, tag.tag_id, tag.size) for tag in page_geometry(config).tags]


__all__ = (
    "alignment_tag_placements",
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
