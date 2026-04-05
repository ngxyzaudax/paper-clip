from common.color_picker import ordered_print_palette
from common.config import PaperClipConfig
from common.types import RGB


def dot_fill_fraction(dot_gain_factor: float) -> float:
    return 1.0 / dot_gain_factor


BLANK_RGB: RGB = (255, 255, 255)


def generate_palette(num_colors: int) -> list[RGB]:
    return ordered_print_palette(num_colors)


def palette_from_config(config: PaperClipConfig) -> list[RGB]:
    return generate_palette(config.num_colors)
