from PIL import Image, ImageDraw

from common.config import CALIBRATION_BAR_ROWS, PaperClipConfig
from common.drawing import draw_dot_cell
from common.page_layout import calibration_region, margin_offset
from common.palette import palette_from_config
from common.symbols import symbol_count


def render_calibration_bar(
    image: Image.Image, config: PaperClipConfig
) -> Image.Image:
    draw = ImageDraw.Draw(image)
    mx, my = margin_offset(config)
    region = calibration_region(config)
    cell = config.cell_size_px
    palette = palette_from_config(config)
    total_symbols = symbol_count(config.num_colors)
    x_base = mx + region.x
    y_base = my + region.y
    for repetition in range(CALIBRATION_BAR_ROWS):
        y = y_base + repetition * cell
        for sym_idx in range(total_symbols):
            x = x_base + sym_idx * cell
            if x + cell > mx + region.x + region.width:
                break
            color = palette[sym_idx - 1] if sym_idx > 0 else None
            draw_dot_cell(draw, x, y, cell, color)
    return image
