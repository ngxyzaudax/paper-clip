from PIL import Image, ImageDraw

from common.config import PaperClipConfig
from common.page_layout import data_grid_region, margin_offset


def render_timing_tracks(image: Image.Image, config: PaperClipConfig) -> Image.Image:
    draw = ImageDraw.Draw(image)
    mx, my = margin_offset(config)
    data_region = data_grid_region(config)
    cell = config.cell_size_px
    _draw_horizontal_track(draw, mx, my, data_region, cell)
    _draw_vertical_track(draw, mx, my, data_region, cell)
    return image


def _draw_horizontal_track(
    draw: ImageDraw.ImageDraw,
    mx: int,
    my: int,
    data_region: "Region",
    cell: int,
) -> None:
    y_start = my + data_region.y - cell
    x_start = mx + data_region.x
    num_cells = data_region.width // cell
    for i in range(num_cells):
        color = (0, 0, 0) if i % 2 == 0 else (255, 255, 255)
        x = x_start + i * cell
        draw.rectangle([x, y_start, x + cell - 1, y_start + cell - 1], fill=color)


def _draw_vertical_track(
    draw: ImageDraw.ImageDraw,
    mx: int,
    my: int,
    data_region: "Region",
    cell: int,
) -> None:
    x_start = mx + data_region.x - cell
    y_start = my + data_region.y
    num_cells = data_region.height // cell
    for i in range(num_cells):
        color = (0, 0, 0) if i % 2 == 0 else (255, 255, 255)
        y = y_start + i * cell
        draw.rectangle([x_start, y, x_start + cell - 1, y + cell - 1], fill=color)
