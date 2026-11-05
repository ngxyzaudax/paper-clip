from PIL import Image

from common.config import PaperClipConfig
from common.format_spec import FLAG_DUPLEX
from common.qr_scale import flags_with_qr_mm
from common.tag_scale import flags_with_tag_mm
from common.page_layout import page_image_size
from common.types import SymbolGrid
from serialization.encode.alignment import draw_apriltag_layer
from serialization.encode.calibration import render_calibration_strip
from serialization.encode.frame_payload import PreparedPayload
from serialization.encode.grid_renderer import render_data_grid
from serialization.encode.grid_header import place_grid_header
from serialization.encode.header_bytes import encode_header_bytes
from serialization.encode.qr_render import render_qr_headers


def render_page(
    grid: SymbolGrid,
    page_index: int,
    total_pages: int,
    data_pages: int,
    prepared: PreparedPayload,
    config: PaperClipConfig,
    duplex: bool = False,
) -> Image.Image:
    width, height = page_image_size(config)
    image = Image.new("RGB", (width, height), (255, 255, 255))
    header = encode_header_bytes(
        config,
        page_index,
        total_pages,
        data_pages,
        len(prepared.payload),
        prepared.original_length,
        prepared.original_sha256,
        page_flags(prepared, config, duplex),
    )
    image = render_data_grid(place_grid_header(grid, header, config), image, config)
    image = render_calibration_strip(image, config)
    image = render_qr_headers(header, image, config)
    return draw_apriltag_layer(image, config)


def page_flags(prepared: PreparedPayload, config: PaperClipConfig, duplex: bool) -> int:
    flags = flags_with_qr_mm(flags_with_tag_mm(prepared.flags, config.tag_size_mm), config.qr_module_mm)
    return flags | FLAG_DUPLEX if duplex else flags
