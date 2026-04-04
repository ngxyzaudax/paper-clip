import numpy as np
from PIL import Image

from common.config import PaperClipConfig
from common.page_layout import margin_offset, rainbow_region
from common.palette import palette_from_config
from common.types import RGB

GRAYSCALE_LEVELS = [0, 28, 56, 85, 113, 142, 170, 198, 226, 255]


def _hue_to_rgb(hue: float) -> tuple[int, int, int]:
    h = hue % 360
    c = 255
    x = int(c * (1 - abs((h / 60) % 2 - 1)))
    if h < 60:
        return (c, x, 0)
    if h < 120:
        return (x, c, 0)
    if h < 180:
        return (0, c, x)
    if h < 240:
        return (0, x, c)
    if h < 300:
        return (x, 0, c)
    return (c, 0, x)


def _desaturate(rgb: RGB, factor: float = 0.5) -> RGB:
    gray = int(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
    return (
        int(rgb[0] * factor + gray * (1 - factor)),
        int(rgb[1] * factor + gray * (1 - factor)),
        int(rgb[2] * factor + gray * (1 - factor)),
    )


def _build_gradient_row(width: int, height: int) -> np.ndarray:
    hues = np.linspace(0, 360, width, endpoint=False)
    row = np.array([_hue_to_rgb(h) for h in hues], dtype=np.uint8)
    return np.tile(row, (height, 1, 1))


def _build_palette_row(
    width: int, height: int, palette: list[RGB],
) -> np.ndarray:
    row = np.full((height, width, 3), 255, dtype=np.uint8)
    if not palette:
        return row
    cell_w = max(1, width // len(palette))
    for i, color in enumerate(palette):
        x_start = i * cell_w
        x_end = min(width, (i + 1) * cell_w)
        row[:, x_start:x_end] = color
    return row


def _build_grayscale_row(width: int, height: int) -> np.ndarray:
    row = np.full((height, width, 3), 255, dtype=np.uint8)
    cell_w = max(1, width // len(GRAYSCALE_LEVELS))
    for i, level in enumerate(GRAYSCALE_LEVELS):
        x_start = i * cell_w
        x_end = min(width, (i + 1) * cell_w)
        row[:, x_start:x_end] = (level, level, level)
    return row


def _build_desaturated_row(
    width: int, height: int, palette: list[RGB],
) -> np.ndarray:
    desaturated = [_desaturate(c, 0.5) for c in palette]
    return _build_palette_row(width, height, desaturated)


def render_rainbow_strip(
    image: Image.Image, config: PaperClipConfig,
) -> Image.Image:
    mx, my = margin_offset(config)
    region = rainbow_region(config)
    if region.width < 40 or region.height < 16:
        return image

    palette = palette_from_config(config)
    row_h = max(4, region.height // 4)
    remaining_h = region.height - 3 * row_h

    gradient = _build_gradient_row(region.width, row_h)
    palette_row = _build_palette_row(region.width, row_h, palette)
    grayscale = _build_grayscale_row(region.width, row_h)
    desaturated = _build_desaturated_row(region.width, remaining_h, palette)

    combined = np.vstack([gradient, palette_row, grayscale, desaturated])
    strip_img = Image.fromarray(combined, "RGB")
    image.paste(strip_img, (mx + region.x, my + region.y))
    return image
