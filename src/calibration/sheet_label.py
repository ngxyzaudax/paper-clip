from PIL import Image, ImageDraw, ImageFont

from common.geometry_measure import mm_to_px

_SIDE_X_MM = 16.0
_TITLE_X_MM = 66.0
_TOP_MM = 6.5


def draw_side_label(page: Image.Image, side: str, dpi: int) -> None:
    """Print the side name and a title between the top frame tags so a person can tell the faces apart."""
    draw = ImageDraw.Draw(page)
    top = mm_to_px(_TOP_MM, dpi)
    draw.text((mm_to_px(_SIDE_X_MM, dpi), top), side.upper(), fill=(0, 0, 0), font=_font(4.2, dpi))
    draw.text(
        (mm_to_px(_TITLE_X_MM, dpi), top + mm_to_px(0.8, dpi)),
        "paper-clip calibration",
        fill=(90, 90, 90),
        font=_font(2.6, dpi),
    )


def _font(height_mm: float, dpi: int) -> ImageFont.FreeTypeFont:
    return ImageFont.load_default(size=mm_to_px(height_mm, dpi))
