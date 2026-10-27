from PIL import ImageDraw

from common.format_spec import DOT_DIAMETER_RATIO


def dot_radius_px(cell_size: int) -> int:
    return max(1, int(cell_size * DOT_DIAMETER_RATIO / 2))


def draw_dot_cell(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    cell_size: int,
    color: tuple[int, int, int] | None,
) -> None:
    draw.rectangle([x, y, x + cell_size - 1, y + cell_size - 1], fill=(255, 255, 255))
    if color is None:
        return
    radius = dot_radius_px(cell_size)
    cx = x + cell_size // 2
    cy = y + cell_size // 2
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius - 1, cy + radius - 1],
        fill=color,
    )
