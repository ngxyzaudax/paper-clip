from PIL import Image

from common.config import PaperClipConfig
from common.page_layout import page_image_size
from common.types import PageInfo, SymbolGrid
from serialization.encode.alignment import draw_finder_patterns
from serialization.encode.calibration import render_calibration_bar
from serialization.encode.grid_renderer import render_data_grid
from serialization.encode.info_panel import render_info_panel
from serialization.encode.palette_qr import render_palette_qr
from serialization.encode.qr_header import render_qr_header, encode_header_bytes
from serialization.encode.rainbow_strip import render_rainbow_strip
from serialization.encode.timing import render_timing_tracks


def render_page(
    grid: SymbolGrid,
    page_index: int,
    total_pages: int,
    data_pages: int,
    data_hash: bytes,
    data_length: int,
    config: PaperClipConfig,
    flags: int = 0,
    page_info: PageInfo | None = None,
) -> Image.Image:
    width, height = page_image_size(config)
    image = Image.new("RGB", (width, height), (255, 255, 255))
    image = draw_finder_patterns(image, config)
    header_bytes = encode_header_bytes(
        config, page_index, total_pages, data_pages, data_hash, data_length, flags
    )
    image = render_qr_header(header_bytes, image, config)
    image = render_palette_qr(image, config)
    image = render_calibration_bar(image, config)
    image = render_rainbow_strip(image, config)
    image = render_timing_tracks(image, config)
    image = render_data_grid(grid, image, config)
    if page_info is not None:
        image = render_info_panel(image, config, page_info)
    return image
