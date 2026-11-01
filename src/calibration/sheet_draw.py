from dataclasses import replace

from PIL import Image, ImageDraw

from calibration.sheet_field import field_rect, symbol_grid, tag_centers
from calibration.sheet_label import draw_side_label
from calibration.sheet_spec import FRAME_TAG_MM, PAGE_H_MM, PAGE_W_MM, Patch, SheetSide
from common.apriltag_markers import render_apriltag
from common.config import default_config
from common.drawing import draw_dot_cell
from common.geometry_measure import mm_to_px
from common.qr_scale import flags_with_qr_mm
from serialization.decode.nearest_colour import blank_and_palette
from serialization.encode.qr_header import encode_header_bytes, qr_image


def draw_side(side: SheetSide, dpi: int = 720) -> Image.Image:
    page = Image.new("RGB", (mm_to_px(PAGE_W_MM, dpi), mm_to_px(PAGE_H_MM, dpi)), (255, 255, 255))
    for tag in side.frame:
        _paste_tag(page, tag.tag_id, tag.x_mm, tag.y_mm, FRAME_TAG_MM, dpi)
    draw_side_label(page, side.name, dpi)
    for patch in side.patches:
        _draw_patch(page, patch, dpi)
    return page


def _draw_patch(page: Image.Image, patch: Patch, dpi: int) -> None:
    if patch.kind == "qr":
        _paste_qr(page, patch, dpi)
        return
    _paste_dots(page, patch, dpi)
    for tag_id, (x_mm, y_mm) in tag_centers(patch).items():
        _paste_tag(page, tag_id, x_mm, y_mm, patch.tag_mm, dpi)


def _paste_tag(page: Image.Image, tag_id: int, x_mm: float, y_mm: float, tag_mm: float, dpi: int) -> None:
    size = max(8, mm_to_px(tag_mm, dpi))
    sprite = render_apriltag(tag_id, size).convert("RGB")
    left = mm_to_px(x_mm, dpi) - size // 2
    top = mm_to_px(y_mm, dpi) - size // 2
    page.paste(sprite, (left, top))


def _paste_qr(page: Image.Image, patch: Patch, dpi: int) -> None:
    config = replace(default_config(), qr_module_mm=patch.qr_mm)
    blob = encode_header_bytes(
        config, 0, 1, 1, 8, 4, b"\x22" * 32, flags_with_qr_mm(0, patch.qr_mm),
    )
    sprite = qr_image(blob, dpi, patch.qr_mm).convert("RGB")
    page.paste(sprite, (mm_to_px(patch.x_mm, dpi), mm_to_px(patch.y_mm, dpi)))


def _paste_dots(page: Image.Image, patch: Patch, dpi: int) -> None:
    if dpi != 720:
        raise ValueError("calibration dots are laid out at 720 dpi")
    colours = blank_and_palette(replace(default_config(), num_symbols=patch.symbols))
    x0, y0, _width, _height = field_rect(patch)
    origin = (mm_to_px(x0, dpi), mm_to_px(y0, dpi))
    for row, line in enumerate(symbol_grid(patch)):
        for col, symbol in enumerate(line):
            if symbol <= 0:
                continue
            cell = Image.new("RGB", (patch.cell_px, patch.cell_px), (255, 255, 255))
            draw_dot_cell(ImageDraw.Draw(cell), 0, 0, patch.cell_px, colours[symbol], patch.dot_ratio)
            page.paste(cell, (origin[0] + col * patch.cell_px, origin[1] + row * patch.cell_px))
