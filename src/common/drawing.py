from PIL import ImageDraw

from common.palette import dot_fill_fraction


def draw_dot_cell(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    cell_size: int,
    color: tuple[int, int, int] | None,
    dot_gain_factor: float,
    guard_band_px: int,
) -> None:
    draw.rectangle([x, y, x + cell_size - 1, y + cell_size - 1], fill=(255, 255, 255))
    if color is None:
        return
    inner = cell_size - 2 * guard_band_px
    fill = dot_fill_fraction(dot_gain_factor)
    radius = max(1, int(inner * fill / 2))
    cx = x + cell_size // 2
    cy = y + cell_size // 2
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)
