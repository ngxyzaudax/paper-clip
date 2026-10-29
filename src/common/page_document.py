import io
from pathlib import Path

from PIL import Image

from common.device_error import DeviceError
from common.ipp_options import PrintTicket
from common.pwg_header import pwg_page


def render_document(page: Path, ticket: PrintTicket) -> bytes:
    image = Image.open(page).convert("RGB")
    width = ticket.media.points[0] * ticket.dpi // 72
    height = ticket.media.points[1] * ticket.dpi // 72
    resized = image.resize((width, height), Image.Resampling.LANCZOS)
    if ticket.document_format == "image/pwg-raster":
        return pwg_page(resized.tobytes(), width, height, ticket.dpi, ticket.media.points, ticket.media.keyword)
    if ticket.document_format == "image/jpeg":
        return _jpeg(resized)
    raise DeviceError(f"unsupported driverless document format: {ticket.document_format}")


def _jpeg(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95, subsampling=0)
    return buffer.getvalue()
