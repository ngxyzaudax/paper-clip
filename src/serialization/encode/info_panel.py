from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common.config import FORMAT_VERSION, FLAG_ENCRYPTED, PaperClipConfig
from common.page_layout import (
    data_capacity_bytes,
    grid_dimensions,
    info_region,
    margin_offset,
)
from common.types import PageInfo

_MONO_FONT_PATHS = [
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]

_FONT_PT = 3


def _load_mono_font(dpi: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size_px = max(12, int(_FONT_PT * dpi / 72))
    for path in _MONO_FONT_PATHS:
        if Path(path).exists():
            return ImageFont.truetype(path, size_px)
    return ImageFont.load_default()


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def _page_type_label(info: PageInfo) -> str:
    if info.total_pages == 1:
        return "single page"
    if info.page_index < info.data_pages:
        return f"data page {info.page_index + 1}/{info.data_pages}"
    return f"parity page {info.page_index - info.data_pages + 1}/{info.total_pages - info.data_pages}"


def _build_info_lines(info: PageInfo, config: PaperClipConfig) -> list[str]:
    cols, rows = grid_dimensions(config)
    cap = data_capacity_bytes(config)
    sha_full = info.sha256_hash.hex()
    flags_parts = []
    if info.encrypted:
        flags_parts.append("ENC")
    if config.redundancy_pages > 0:
        flags_parts.append(f"+{config.redundancy_pages}P")
    flags_str = " [" + " ".join(flags_parts) + "]" if flags_parts else ""

    line1 = (
        f"Paper-Clip v{FORMAT_VERSION}  |  "
        f"{info.filename} ({_format_size(info.file_size)})  |  "
        f"{_page_type_label(info)}  |  "
        f"{info.timestamp}{flags_str}"
    )
    line2 = (
        f"{config.num_colors} colors  |  "
        f"cell {config.cell_size_px}px  |  "
        f"RS {config.rs_redundancy:.0%}  |  "
        f"{cols}x{rows} grid ({cols * rows:,} cells)  |  "
        f"{_format_size(cap)}/page  |  "
        f"SHA256:{sha_full}"
    )
    return [line1, line2]


def render_info_panel(
    image: Image.Image,
    config: PaperClipConfig,
    info: PageInfo,
) -> Image.Image:
    draw = ImageDraw.Draw(image)
    mx, my = margin_offset(config)
    region = info_region(config)
    font = _load_mono_font(config.scan_dpi)
    lines = _build_info_lines(info, config)
    text_color = (80, 80, 80)
    line_height = int(_FONT_PT * config.scan_dpi / 72 * 1.35)
    x = mx + region.x + 10
    y_start = my + region.y + 8
    for i, line in enumerate(lines):
        draw.text((x, y_start + i * line_height), line, fill=text_color, font=font)
    return image
