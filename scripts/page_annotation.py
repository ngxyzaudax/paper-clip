import numpy as np
from PIL import Image, ImageDraw, ImageFont

from common.config import PaperClipConfig
from common.geometry import PageGeometry, page_geometry
from common.geometry_shift import tag_box
from common.geometry_tags import tag_quiet_px
from common.page_capacity import data_capacity_symbols

Box = tuple[float, float, float, float]

MARGIN = (90, 90, 90, 120)
DATA = (0, 150, 60, 255)
QR = (220, 30, 30, 70)
STRIP = (255, 140, 0, 255)
TAG = (30, 90, 230, 60)
BLOCK = (140, 40, 180, 255)


def layout_rows(config: PaperClipConfig) -> list[tuple[str, str]]:
    g = page_geometry(config)
    mm = _mm(config)
    right = g.page_w - g.origin_x - g.usable_w
    bottom = g.page_h - g.origin_y - g.usable_h
    return [
        ("page", f"{mm(g.page_w)} x {mm(g.page_h)} mm"),
        ("margins", f"left {mm(g.origin_x)}, top {mm(g.origin_y)}, right {mm(right)}, bottom {mm(bottom)} mm"),
        ("data area", f"{_box_mm(mm, _page_box(g, (0, 0, g.usable_w, g.usable_h)))}"),
        ("cells", f"{g.cols} x {g.rows} grid of {mm(g.cell)} mm, {data_capacity_symbols(config)} data cells"),
        ("qr", _box_mm(mm, _page_box(g, g.qr))),
        ("strip", _box_mm(mm, _page_box(g, g.calibration))),
        ("centre block", _box_mm(mm, _page_box(g, g.centre))),
        ("tags", f"{len(g.tags)} of {g.tag_rows} x {g.tag_cols}, {mm(g.tags[0].size)} mm"),
    ]


def annotate_page(page: np.ndarray, config: PaperClipConfig, scale: int = 2) -> Image.Image:
    g = page_geometry(config)
    base = Image.fromarray(page).convert("RGBA")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    usable = _page_box(g, (0, 0, g.usable_w, g.usable_h))
    _shade_margins(draw, usable, g.page_w, g.page_h)
    line = max(4, g.cell // 4)
    draw.rectangle(_corners(usable), outline=DATA, width=line)
    draw.rectangle(_corners(_page_box(g, g.centre)), outline=BLOCK, width=line)
    draw.rectangle(_corners(_page_box(g, g.qr)), fill=QR, outline=QR[:3] + (255,), width=line)
    draw.rectangle(_corners(_page_box(g, g.calibration)), outline=STRIP, width=line)
    quiet = tag_quiet_px(config.print_dpi)
    for tag in g.tags:
        draw.rectangle(_corners(_page_box(g, tag_box(tag, quiet))), fill=TAG, outline=TAG[:3] + (255,), width=line)
    _labels(draw, g, config, usable)
    merged = Image.alpha_composite(base, layer).convert("RGB")
    return merged.resize((g.page_w // scale, g.page_h // scale), Image.Resampling.LANCZOS)


def _labels(draw: ImageDraw.ImageDraw, g: PageGeometry, config: PaperClipConfig, usable: Box) -> None:
    mm = _mm(config)
    font = ImageFont.load_default(size=max(24, g.page_w // 50))
    qr, strip, block = (_page_box(g, region) for region in (g.qr, g.calibration, g.centre))
    _tag(draw, font, (qr[0], qr[1] - 2.2 * font.size), f"QR header {mm(qr[2])} mm", QR[:3])
    _tag(draw, font, (block[0] + block[2] + font.size, strip[1]), "calibration strip", STRIP[:3])
    _tag(draw, font, (block[0], block[1] + block[3] + 0.6 * font.size), "centre keep-out", BLOCK[:3])
    _tag(draw, font, (usable[0] + g.cell, usable[1] + usable[3] - 2.6 * font.size), "data area", DATA[:3])
    _tag(draw, font, (usable[0], 0.1 * font.size), f"margin {mm(g.origin_y)} mm", MARGIN[:3])
    first = g.tags[0]
    _tag(draw, font, _page_box(g, (first.x + first.size + g.cell, first.y, 0, 0))[:2], "AprilTag + quiet zone", TAG[:3])


def _tag(draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont, at: tuple[float, float], text: str, colour) -> None:
    box = draw.textbbox(at, text, font=font)
    pad = font.size // 4
    draw.rectangle((box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad), fill=(255, 255, 255, 230), outline=colour + (255,), width=3)
    draw.text(at, text, font=font, fill=colour + (255,))


def _shade_margins(draw: ImageDraw.ImageDraw, usable: Box, width: int, height: int) -> None:
    x0, y0, x1, y1 = _corners(usable)
    for rect in ((0, 0, width, y0), (0, y1, width, height), (0, y0, x0, y1), (x1, y0, width, y1)):
        draw.rectangle(rect, fill=MARGIN)


def _page_box(g: PageGeometry, region) -> Box:
    x, y, w, h = region
    return (g.origin_x + x, g.origin_y + y, w, h)


def _corners(box: Box) -> tuple[float, float, float, float]:
    return (box[0], box[1], box[0] + box[2] - 1, box[1] + box[3] - 1)


def _box_mm(mm, box: Box) -> str:
    return f"x {mm(box[0])}, y {mm(box[1])}, {mm(box[2])} x {mm(box[3])} mm"


def _mm(config: PaperClipConfig):
    return lambda px: f"{px * 25.4 / config.print_dpi:.2f}"
