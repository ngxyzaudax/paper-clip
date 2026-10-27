import base64
import zlib
from typing import NamedTuple

import qrcode
from PIL import Image
from qrcode.constants import ERROR_CORRECT_H

from common.codec import calculate_ecc_symbols
from common.config import BLOCK_SIZE, PaperClipConfig
from common.format_spec import (
    HEADER_BODY,
    HEADER_STRUCT,
    MAGIC,
    QR_BORDER_MODULES,
    QR_VERSION,
)
from common.geometry_measure import hundredths_to_mm, mm_to_hundredths
from common.geometry_qr import qr_module_px
from common.page_layout import grid_dimensions, margin_offset, qr_region


class DecodedQrHeader(NamedTuple):
    tag_pitch_mm: int
    flags: int
    num_symbols: int
    cell_size_px: int
    ecc_sym: int
    print_dpi: int
    margin_top_mm: float
    margin_right_mm: float
    margin_bottom_mm: float
    margin_left_mm: float
    page_width_mm: float
    page_height_mm: float
    cols: int
    rows: int
    page_index: int
    total_pages: int
    data_pages: int
    payload_length: int
    original_length: int
    original_sha256: bytes


def encode_header_bytes(
    config: PaperClipConfig,
    page_index: int,
    total_pages: int,
    data_pages: int,
    payload_length: int,
    original_length: int,
    original_sha256: bytes,
    flags: int,
) -> bytes:
    cols, rows = grid_dimensions(config)
    body = HEADER_BODY.pack(
        MAGIC,
        int(round(config.tag_pitch_mm)),
        flags,
        config.num_symbols,
        config.cell_size_px,
        calculate_ecc_symbols(BLOCK_SIZE, config.rs_redundancy),
        config.print_dpi,
        mm_to_hundredths(config.margin_top_mm),
        mm_to_hundredths(config.margin_right_mm),
        mm_to_hundredths(config.margin_bottom_mm),
        mm_to_hundredths(config.margin_left_mm),
        mm_to_hundredths(config.page_width_mm),
        mm_to_hundredths(config.page_height_mm),
        cols,
        rows,
        page_index,
        total_pages,
        data_pages,
        payload_length,
        original_length,
        original_sha256,
    )
    return body + (zlib.crc32(body) & 0xFFFFFFFF).to_bytes(4, "big")


def decode_header_bytes(blob: bytes) -> DecodedQrHeader:
    if len(blob) != HEADER_STRUCT.size:
        raise ValueError("invalid header length")
    unpacked = HEADER_STRUCT.unpack(blob)
    magic = unpacked[0]
    crc = unpacked[-1]
    if magic != MAGIC:
        raise ValueError("invalid header magic")
    if (zlib.crc32(blob[:-4]) & 0xFFFFFFFF) != crc:
        raise ValueError("invalid header crc")
    return DecodedQrHeader(
        tag_pitch_mm=unpacked[1],
        flags=unpacked[2],
        num_symbols=unpacked[3],
        cell_size_px=unpacked[4],
        ecc_sym=unpacked[5],
        print_dpi=unpacked[6],
        margin_top_mm=hundredths_to_mm(unpacked[7]),
        margin_right_mm=hundredths_to_mm(unpacked[8]),
        margin_bottom_mm=hundredths_to_mm(unpacked[9]),
        margin_left_mm=hundredths_to_mm(unpacked[10]),
        page_width_mm=hundredths_to_mm(unpacked[11]),
        page_height_mm=hundredths_to_mm(unpacked[12]),
        cols=unpacked[13],
        rows=unpacked[14],
        page_index=unpacked[15],
        total_pages=unpacked[16],
        data_pages=unpacked[17],
        payload_length=unpacked[18],
        original_length=unpacked[19],
        original_sha256=unpacked[20],
    )


def header_to_qr_payload(header_bytes: bytes) -> str:
    return base64.b64encode(header_bytes).decode("ascii")


def qr_image(header_bytes: bytes, dpi: int) -> Image.Image:
    module = qr_module_px(dpi)
    qr = qrcode.QRCode(
        version=QR_VERSION,
        error_correction=ERROR_CORRECT_H,
        box_size=module,
        border=QR_BORDER_MODULES,
    )
    qr.add_data(header_to_qr_payload(header_bytes))
    qr.make(fit=False)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def render_qr_header(header_bytes: bytes, image: Image.Image, config: PaperClipConfig) -> Image.Image:
    qr_img = qr_image(header_bytes, config.print_dpi)
    mx, my = margin_offset(config)
    region = qr_region(config)
    if qr_img.size != (region.width, region.height):
        raise ValueError(
            f"QR image {qr_img.size} does not match the header slot {(region.width, region.height)}"
        )
    image.paste(qr_img, (mx + region.x, my + region.y))
    return image
