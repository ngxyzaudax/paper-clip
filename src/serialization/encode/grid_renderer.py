from PIL import Image, ImageDraw

from common.config import PaperClipConfig
from common.drawing import draw_dot_cell
from common.page_layout import data_grid_region, margin_offset
from common.palette import palette_from_config
from common.types import SymbolGrid
from serialization.encode.stripe import STRIPE


def render_data_grid(
    grid: SymbolGrid, image: Image.Image, config: PaperClipConfig
) -> Image.Image:
    draw = ImageDraw.Draw(image)
    mx, my = margin_offset(config)
    region = data_grid_region(config)
    cell = config.cell_size_px
    palette = palette_from_config(config)
    x_base = mx + region.x
    y_base = my + region.y
    for row_idx, row in enumerate(grid):
        for col_idx, symbol_idx in enumerate(row):
            x = x_base + col_idx * cell
            y = y_base + row_idx * cell
            if symbol_idx == STRIPE:
                draw.rectangle([x, y, x + cell - 1, y + cell - 1], fill=(0, 0, 0))
                continue
            if symbol_idx < 0:
                continue
            color = palette[symbol_idx - 1] if symbol_idx > 0 else None
            draw_dot_cell(draw, x, y, cell, color, config.dot_ratio)
    return image
