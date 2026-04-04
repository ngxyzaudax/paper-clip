import base64
import zlib

import qrcode
from PIL import Image
from qrcode.constants import ERROR_CORRECT_M

from common.config import PALETTE_QR_BORDER, PALETTE_QR_MODULE_PX, PaperClipConfig
from common.page_layout import margin_offset, metadata_band_height, palette_qr_region
from common.types import RGB

PALETTE_MAGIC = b"PLTE"


def encode_palette_bytes(colors: tuple[tuple[int, int, int], ...]) -> bytes:
    payload = PALETTE_MAGIC + bytes([len(colors)])
    for r, g, b in colors:
        payload += bytes([r, g, b])
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    return payload + crc.to_bytes(4, "big")


def decode_palette_bytes(data: bytes) -> tuple[RGB, ...] | None:
    if len(data) < 9 or data[:4] != PALETTE_MAGIC:
        return None
    num_colors = data[4]
    expected_len = 5 + 3 * num_colors + 4
    if len(data) < expected_len:
        return None
    payload = data[: expected_len - 4]
    stored_crc = int.from_bytes(data[expected_len - 4 : expected_len], "big")
    if zlib.crc32(payload) & 0xFFFFFFFF != stored_crc:
        return None
    colors: list[RGB] = []
    for i in range(num_colors):
        offset = 5 + 3 * i
        colors.append((data[offset], data[offset + 1], data[offset + 2]))
    return tuple(colors)


def palette_to_qr_payload(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def qr_payload_to_palette(qr_data: bytes) -> bytes | None:
    try:
        return base64.b64decode(qr_data)
    except Exception:
        return None


def render_palette_qr(
    image: Image.Image, config: PaperClipConfig,
) -> Image.Image:
    if not config.calibrated_colors:
        return image
    region = palette_qr_region(config)
    if region.width == 0:
        return image
    raw = encode_palette_bytes(config.calibrated_colors)
    qr = qrcode.QRCode(
        error_correction=ERROR_CORRECT_M,
        box_size=PALETTE_QR_MODULE_PX,
        border=PALETTE_QR_BORDER,
    )
    qr.add_data(palette_to_qr_payload(raw))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    mx, my = margin_offset(config)
    band_h = metadata_band_height(config)
    qr_h = qr_img.size[1]
    y_offset = (band_h - qr_h) // 2
    image.paste(qr_img, (mx + region.x, my + region.y + y_offset))
    return image
