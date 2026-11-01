import io
from pathlib import Path

from PIL import Image

from common.device_error import DeviceError
from common.ipp_options import PrintTicket
from common.pwg_back import orient_raster, raster_extent, raster_transform
from common.pwg_header import pwg_page


def render_document(page: Path, ticket: PrintTicket) -> bytes:
    image = Image.open(page).convert("RGB")
    width, height = _pixels(ticket)
    resized = image.resize((width, height), Image.Resampling.LANCZOS)
    if ticket.document_format == "image/pwg-raster":
        return _pwg(resized.tobytes(), width, height, ticket)
    if ticket.document_format == "image/jpeg":
        return _jpeg(resized)
    raise DeviceError(f"unsupported driverless document format: {ticket.document_format}")


def render_pages(pages: list[Path], ticket: PrintTicket) -> bytes:
    if len(pages) > 1 and ticket.document_format != "image/pwg-raster":
        raise DeviceError("only a PWG raster document can carry both sides of one sheet")
    total = len(pages)
    return b"".join(_indexed(page, ticket, index, total) for index, page in enumerate(pages))


def _indexed(page: Path, ticket: PrintTicket, index: int, total: int) -> bytes:
    return render_document(page, ticket._replace(page_index=index, page_count=total))


def _pixels(ticket: PrintTicket) -> tuple[int, int]:
    if ticket.document_format == "image/pwg-raster":
        return raster_extent(ticket.media.hundredths, ticket.dpi)
    return (ticket.media.points[0] * ticket.dpi // 72, ticket.media.points[1] * ticket.dpi // 72)


def _pwg(raw: bytes, width: int, height: int, ticket: PrintTicket) -> bytes:
    cross, feed = raster_transform(ticket.sides, ticket.sheet_back, ticket.page_index)
    return pwg_page(
        orient_raster(raw, width, height, cross, feed),
        width,
        height,
        ticket.dpi,
        raster_extent(ticket.media.hundredths, 72),
        ticket.media.keyword,
        ticket.sides,
        ticket.page_count,
        cross,
        feed,
    )


def _jpeg(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95, subsampling=0)
    return buffer.getvalue()
