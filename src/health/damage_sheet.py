from PIL import Image, ImageDraw, ImageFont

from health.damage_overlay import DAMAGED_RGB, LOST_HEADER_RGB, UNSURE_RGB

BACKGROUND_RGB = (255, 255, 255)
TEXT_RGB = (20, 20, 20)
MUTED_RGB = (90, 90, 90)
REFERENCE_WIDTH_PX = 1600
GAP_PX = 40
TITLE_BAND_PX = 190
CAPTION_BAND_PX = 60
TITLE_FONT_PX = 40
TEXT_FONT_PX = 28
LEGEND = (
    (DAMAGED_RGB, "misread cell, repaired by parity"),
    (UNSURE_RGB, "faint cell, read correctly"),
    (LOST_HEADER_RGB, "unreadable QR header"),
)


def damage_sheet(title: str, subtitle: str, panels: list[tuple[Image.Image, str]]) -> Image.Image:
    """Pages side by side under a title and colour legend, each with its own caption."""
    content = sum(image.width for image, _caption in panels) + GAP_PX * (len(panels) + 1)
    unit = max(1.0, content / REFERENCE_WIDTH_PX)
    top = _px(TITLE_BAND_PX + CAPTION_BAND_PX, unit)
    height = top + max(image.height for image, _caption in panels) + GAP_PX
    sheet = Image.new("RGB", (max(content, REFERENCE_WIDTH_PX), height), BACKGROUND_RGB)
    draw = ImageDraw.Draw(sheet)
    _title(draw, title, subtitle, unit)
    _legend(draw, unit)
    _panels(sheet, draw, panels, unit)
    return sheet


def _px(value: float, unit: float) -> int:
    return int(round(value * unit))


def _font(size: int, unit: float) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return ImageFont.load_default(size=_px(size, unit))


def _title(draw: ImageDraw.ImageDraw, title: str, subtitle: str, unit: float) -> None:
    draw.text((GAP_PX, _px(24, unit)), title, fill=TEXT_RGB, font=_font(TITLE_FONT_PX, unit))
    draw.text((GAP_PX, _px(82, unit)), subtitle, fill=MUTED_RGB, font=_font(TEXT_FONT_PX, unit))


def _legend(draw: ImageDraw.ImageDraw, unit: float) -> None:
    left, top, box = GAP_PX, _px(132, unit), _px(28, unit)
    font = _font(TEXT_FONT_PX, unit)
    for colour, label in LEGEND:
        draw.rectangle((left, top, left + box, top + box), fill=colour)
        draw.text((left + _px(40, unit), top - _px(2, unit)), label, fill=TEXT_RGB, font=font)
        left += _px(80, unit) + int(draw.textlength(label, font=font))


def _panels(
    sheet: Image.Image, draw: ImageDraw.ImageDraw, panels: list[tuple[Image.Image, str]], unit: float,
) -> None:
    left = GAP_PX
    font = _font(TEXT_FONT_PX, unit)
    for image, caption in panels:
        draw.text((left, _px(TITLE_BAND_PX + 12, unit)), caption, fill=TEXT_RGB, font=font)
        sheet.paste(image, (left, _px(TITLE_BAND_PX + CAPTION_BAND_PX, unit)))
        left += image.width + GAP_PX
