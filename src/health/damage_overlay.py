import numpy as np
from PIL import Image, ImageDraw

from common.geometry import page_geometry
from common.geometry_types import PageGeometry
from health.page_cells import page_cell_grid
from health.wrong_cells import unsure_symbols
from serialization.decode.header_config import config_from_header
from serialization.decode.observe import PageObservation

DAMAGED_RGB = (214, 31, 38)
UNSURE_RGB = (245, 150, 0)
LOST_HEADER_RGB = (128, 0, 180)
FRAME_RGB = (120, 120, 120)
FADE_TO_WHITE = 0.55
MIN_MARK_PX = 2


def page_overlay(page: PageObservation, wrong: np.ndarray) -> Image.Image:
    """The rectified scan, faded, with misread cells in red and cells the reader doubted but got right in orange."""
    geometry = page_geometry(config_from_header(page.header))
    grid = page_cell_grid(page.header)
    image = Image.fromarray(_faded(page.preview))
    draw = ImageDraw.Draw(image)
    _frame(draw, geometry, page.preview_scale)
    _lost_headers(draw, geometry, page)
    unsure = np.setdiff1d(unsure_symbols(page), wrong)
    _mark(draw, grid[unsure[unsure < len(grid)]], geometry, page, UNSURE_RGB)
    _mark(draw, grid[wrong[wrong < len(grid)]], geometry, page, DAMAGED_RGB)
    return image


def _faded(preview: np.ndarray) -> np.ndarray:
    rgb = preview[..., :3].astype(np.float32)
    return np.clip(rgb * (1.0 - FADE_TO_WHITE) + 255.0 * FADE_TO_WHITE, 0, 255).astype(np.uint8)


def _lost_headers(draw: ImageDraw.ImageDraw, geometry: PageGeometry, page: PageObservation) -> None:
    if not page.qr_slots_read:
        return
    scale = page.preview_scale
    width = max(2, int(round(geometry.cell * scale * 0.15)))
    for slot, readable in zip(geometry.slots, page.qr_slots_read):
        if readable:
            continue
        left = (geometry.origin_x + slot.qr.x) * scale
        top = (geometry.origin_y + slot.qr.y) * scale
        draw.rectangle(
            (left, top, left + slot.qr.width * scale, top + slot.qr.height * scale),
            outline=LOST_HEADER_RGB,
            width=width,
        )


def _frame(draw: ImageDraw.ImageDraw, geometry: PageGeometry, scale: float) -> None:
    left, top = geometry.origin_x * scale, geometry.origin_y * scale
    right = (geometry.origin_x + geometry.cols * geometry.cell) * scale
    bottom = (geometry.origin_y + geometry.rows * geometry.cell) * scale
    draw.rectangle((left, top, right, bottom), outline=FRAME_RGB, width=1)


def _mark(
    draw: ImageDraw.ImageDraw,
    cells: np.ndarray,
    geometry: PageGeometry,
    page: PageObservation,
    colour: tuple[int, int, int],
) -> None:
    scale = page.preview_scale
    size = max(MIN_MARK_PX, geometry.cell * scale)
    shift_x, shift_y = page.cell_shift
    for row, col in cells:
        left = (geometry.origin_x + int(col) * geometry.cell + shift_x) * scale
        top = (geometry.origin_y + int(row) * geometry.cell + shift_y) * scale
        draw.rectangle((left, top, left + size, top + size), fill=colour)
