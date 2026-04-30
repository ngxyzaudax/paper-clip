from PIL import ImageDraw

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
    radius = max(1, int(cell_size / 2))
    cx = x + cell_size // 2
    cy = y + cell_size // 2
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)
