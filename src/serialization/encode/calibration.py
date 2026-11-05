from PIL import Image, ImageDraw

from common.config import PaperClipConfig
from common.drawing import draw_dot_cell
from common.geometry import page_geometry
from common.page_layout import margin_offset
from common.palette import palette_from_config
from common.types import Region


def render_calibration_strip(image: Image.Image, config: PaperClipConfig) -> Image.Image:
    geometry = page_geometry(config)
    draw = ImageDraw.Draw(image)
    mx, my = margin_offset(config)
    palette = palette_from_config(config)
    for slot in geometry.slots:
        _draw_strip(draw, slot.calibration, geometry.cal_rows, geometry.cell, config, palette, mx, my)
    return image


def _draw_strip(
    draw: ImageDraw.ImageDraw,
    region: Region,
    rows: int,
    cell: int,
    config: PaperClipConfig,
    palette: list[tuple[int, int, int]],
    mx: int,
    my: int,
) -> None:
    for row in range(rows):
        for symbol in range(config.num_symbols):
            color = palette[symbol - 1] if symbol > 0 else None
            x = mx + region.x + symbol * cell
            y = my + region.y + row * cell
            draw_dot_cell(draw, x, y, cell, color, config.dot_ratio)
