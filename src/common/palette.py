from common.color_picker import ordered_print_palette
from common.config import PaperClipConfig
from common.types import RGB


def generate_palette(num_ink_colors: int) -> list[RGB]:
    return ordered_print_palette(num_ink_colors)


def palette_from_config(config: PaperClipConfig) -> list[RGB]:
    return generate_palette(config.num_symbols - 1)
