from PIL import Image

from common.config import PaperClipConfig
from common.page_layout import page_image_size
from common.types import SymbolGrid
from serialization.encode.alignment import draw_apriltag_layer
from serialization.encode.calibration import render_calibration_strip
from serialization.encode.frame_payload import PreparedPayload
from serialization.encode.grid_renderer import render_data_grid
from serialization.encode.qr_header import encode_header_bytes, render_qr_header


def render_page(
    grid: SymbolGrid,
    page_index: int,
    total_pages: int,
    data_pages: int,
    prepared: PreparedPayload,
    config: PaperClipConfig,
) -> Image.Image:
    width, height = page_image_size(config)
    image = Image.new("RGB", (width, height), (255, 255, 255))
    image = render_data_grid(grid, image, config)
    image = render_calibration_strip(image, config)
    header = encode_header_bytes(
        config,
        page_index,
        total_pages,
        data_pages,
        len(prepared.payload),
        prepared.original_length,
        prepared.original_sha256,
        prepared.flags,
    )
    image = render_qr_header(header, image, config)
    return draw_apriltag_layer(image, config)
