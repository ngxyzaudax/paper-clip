import base64

import qrcode
from PIL import Image
from qrcode.constants import ERROR_CORRECT_H

from common.config import PaperClipConfig
from common.format_spec import QR_BORDER_MODULES, QR_MODULE_MM, QR_VERSION
from common.geometry import page_geometry
from common.geometry_qr import qr_module_px
from common.page_layout import margin_offset


def header_to_qr_payload(header_bytes: bytes) -> str:
    return base64.b64encode(header_bytes).decode("ascii")


def qr_image(header_bytes: bytes, dpi: int, module_mm: float = QR_MODULE_MM) -> Image.Image:
    module = qr_module_px(dpi, module_mm)
    qr = qrcode.QRCode(
        version=QR_VERSION,
        error_correction=ERROR_CORRECT_H,
        box_size=module,
        border=QR_BORDER_MODULES,
    )
    qr.add_data(header_to_qr_payload(header_bytes))
    qr.make(fit=False)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def render_qr_headers(header_bytes: bytes, image: Image.Image, config: PaperClipConfig) -> Image.Image:
    qr_img = qr_image(header_bytes, config.print_dpi, config.qr_module_mm)
    mx, my = margin_offset(config)
    for slot in page_geometry(config).slots:
        region = slot.qr
        if qr_img.size != (region.width, region.height):
            raise ValueError(
                f"QR image {qr_img.size} does not match the header slot {(region.width, region.height)}"
            )
        image.paste(qr_img, (mx + region.x, my + region.y))
    return image
