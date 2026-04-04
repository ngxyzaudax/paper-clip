import base64
import struct
import zlib

import qrcode
from PIL import Image
from qrcode.constants import ERROR_CORRECT_M

from common.config import FORMAT_VERSION, MAGIC, PaperClipConfig, QR_BORDER_MODULES, QR_MODULE_PX, QR_VERSION
from common.page_layout import grid_dimensions, margin_offset, qr_region


def encode_header_bytes(
    config: PaperClipConfig,
    page_index: int,
    total_pages: int,
    data_pages: int,
    sha256_hash: bytes,
    data_length: int,
    flags: int = 0,
) -> bytes:
    from common.codec import calculate_ecc_symbols
    from common.config import BLOCK_SIZE

    cols, rows = grid_dimensions(config)
    ecc_sym = calculate_ecc_symbols(BLOCK_SIZE, config.rs_redundancy)
    payload = struct.pack(
        ">4sBBBBBHHHHHHI32s",
        MAGIC,
        FORMAT_VERSION,
        flags,
        config.num_colors,
        config.cell_size_px,
        ecc_sym,
        config.print_dpi,
        cols,
        rows,
        page_index,
        total_pages,
        data_pages,
        data_length,
        sha256_hash,
    )
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    return payload + struct.pack(">I", crc)


def header_to_qr_payload(header_bytes: bytes) -> str:
    return base64.b64encode(header_bytes).decode("ascii")


def _generate_qr_image(data: bytes) -> Image.Image:
    qr = qrcode.QRCode(
        version=QR_VERSION,
        error_correction=ERROR_CORRECT_M,
        box_size=QR_MODULE_PX,
        border=QR_BORDER_MODULES,
    )
    qr.add_data(header_to_qr_payload(data))
    qr.make(fit=False)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def render_qr_header(
    header_bytes: bytes,
    image: Image.Image,
    config: PaperClipConfig,
) -> Image.Image:
    qr_img = _generate_qr_image(header_bytes)
    mx, my = margin_offset(config)
    region = qr_region(config)
    x = mx + region.x
    y = my + region.y
    qr_resized = qr_img.resize((region.width, region.height), Image.Resampling.NEAREST)
    image.paste(qr_resized, (x, y))
    return image
