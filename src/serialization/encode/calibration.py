from PIL import Image, ImageDraw

from common.config import PaperClipConfig
from common.drawing import draw_dot_cell
from common.geometry import page_geometry
from common.page_layout import margin_offset
from common.palette import palette_from_config


def render_calibration_strip(image: Image.Image, config: PaperClipConfig) -> Image.Image:
    geometry = page_geometry(config)
    draw = ImageDraw.Draw(image)
    mx, my = margin_offset(config)
    palette = palette_from_config(config)
    cell = geometry.cell
    region = geometry.calibration
    for row in range(geometry.cal_rows):
        for symbol in range(config.num_symbols):
            color = palette[symbol - 1] if symbol > 0 else None
            x = mx + region.x + symbol * cell
            y = my + region.y + row * cell
            draw_dot_cell(draw, x, y, cell, color)
    return image
