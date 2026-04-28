import base64
import struct
import zlib
from typing import NamedTuple

import qrcode
from PIL import Image
from qrcode.constants import ERROR_CORRECT_M

from common.codec import calculate_ecc_symbols
from common.config import (
    BLOCK_SIZE,
    HEADER_FORMAT_VERSION,
    HEADER_STRUCT,
    MAGIC,
    PaperClipConfig,
    QR_BORDER_MODULES,
    QR_MODULE_PX,
    QR_VERSION,
)
from common.page_layout import grid_dimensions, margin_offset, qr_region


class DecodedQrHeader(NamedTuple):
    format_version: int
    num_symbols: int
    cell_size_px: int
    ecc_sym: int
    cols: int
    rows: int
    page_index: int
    total_pages: int
    data_pages: int
    payload_sha256: bytes


def encode_header_bytes(
    config: PaperClipConfig,
    page_index: int,
    total_pages: int,
    data_pages: int,
    payload_sha256: bytes,
) -> bytes:
    cols, rows = grid_dimensions(config)
    ecc_sym = calculate_ecc_symbols(BLOCK_SIZE, config.rs_redundancy)
    body = struct.pack(
        ">4sBBBBHHHHH32s",
        MAGIC,
        HEADER_FORMAT_VERSION,
        config.num_symbols,
        config.cell_size_px,
        ecc_sym,
        cols,
        rows,
        page_index,
        total_pages,
        data_pages,
        payload_sha256,
    )
    crc = zlib.crc32(body) & 0xFFFFFFFF
    return body + struct.pack(">I", crc)


def decode_header_bytes(blob: bytes) -> DecodedQrHeader:
    if len(blob) != HEADER_STRUCT.size:
        raise ValueError("invalid header length")
    (
        magic,
        format_version,
        num_symbols,
        cell_size_px,
        ecc_sym,
        cols,
        rows,
        page_index,
        total_pages,
        data_pages,
        payload_sha256,
        crc,
    ) = HEADER_STRUCT.unpack(blob)
    if magic != MAGIC:
        raise ValueError("invalid header magic")
    body = blob[:-4]
    if (zlib.crc32(body) & 0xFFFFFFFF) != crc:
        raise ValueError("invalid header crc")
    return DecodedQrHeader(
        format_version=format_version,
        num_symbols=num_symbols,
        cell_size_px=cell_size_px,
        ecc_sym=ecc_sym,
        cols=cols,
        rows=rows,
        page_index=page_index,
        total_pages=total_pages,
        data_pages=data_pages,
        payload_sha256=payload_sha256,
    )


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
