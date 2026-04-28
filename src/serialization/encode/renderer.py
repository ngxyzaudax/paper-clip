from PIL import Image

from common.config import PaperClipConfig
from common.page_layout import page_image_size
from common.types import SymbolGrid
from serialization.encode.alignment import draw_apriltag_layer
from serialization.encode.grid_renderer import render_data_grid
from serialization.encode.qr_header import render_qr_header, encode_header_bytes


def render_page(
    grid: SymbolGrid,
    page_index: int,
    total_pages: int,
    data_pages: int,
    payload_sha256: bytes,
    config: PaperClipConfig,
) -> Image.Image:
    width, height = page_image_size(config)
    image = Image.new("RGB", (width, height), (255, 255, 255))
    header_bytes = encode_header_bytes(
        config, page_index, total_pages, data_pages, payload_sha256,
    )
    image = render_qr_header(header_bytes, image, config)
    image = render_data_grid(grid, image, config)
    image = draw_apriltag_layer(image, config)
    return image
