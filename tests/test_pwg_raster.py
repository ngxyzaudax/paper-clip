from pathlib import Path

from PIL import Image

from common.ipp_media import MediaSize
from common.ipp_options import PrintTicket
from common.page_document import render_document, render_pages
from common.pwg_back import orient_raster, raster_extent, raster_transform
from common.pwg_header import HEADER_BYTES, SYNC, page_header, pwg_page
from common.pwg_rows import unpack_rows


def test_pwg_page_roundtrip_keeps_pixels_and_page_name() -> None:
    width, height = 4, 3
    raw = bytes([
        255, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255,
        255, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 255, 255,
    ])
    page = pwg_page(raw, width, height, 360, (595, 842), "iso_a4_210x297mm")
    assert page.startswith(SYNC)
    header = page[len(SYNC):len(SYNC) + HEADER_BYTES]
    assert len(header) == HEADER_BYTES
    assert header[1732:1732 + len(b"iso_a4_210x297mm")] == b"iso_a4_210x297mm"
    assert int.from_bytes(header[372:376], "big") == width
    assert int.from_bytes(header[376:380], "big") == height
    assert int.from_bytes(header[276:280], "big") == 360
    assert _floats(header, 424) == (1.0, 595.0, 842.0, 0.0, 0.0, 595.0, 842.0)
    assert unpack_rows(page[len(SYNC) + HEADER_BYTES:], width, height) == raw
    assert page_header(width, height, 360, (595, 842), "iso_a4_210x297mm") == header


def test_page_header_records_the_duplex_edge() -> None:
    single = page_header(4, 3, 360, (595, 842), "iso_a4_210x297mm")
    long_edge = page_header(4, 3, 360, (595, 842), "iso_a4_210x297mm", "two-sided-long-edge")
    short_edge = page_header(4, 3, 360, (595, 842), "iso_a4_210x297mm", "two-sided-short-edge")
    assert _field(single, 272) == 0 and _field(single, 368) == 0
    assert _field(long_edge, 272) == 1 and _field(long_edge, 368) == 0
    assert _field(short_edge, 272) == 1 and _field(short_edge, 368) == 1


def test_rotated_duplex_document_has_two_long_edge_headers(tmp_path: Path) -> None:
    front = _png(tmp_path / "front.png", bytes([255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 255]))
    back = _png(tmp_path / "back.png", bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]))
    ticket = _ticket("rotated")
    document = render_pages([front, back], ticket)
    front_page = render_document(front, ticket._replace(page_index=0, page_count=2))
    back_page = render_document(back, ticket._replace(page_index=1, page_count=2))
    assert document == front_page + back_page
    assert front_page.startswith(SYNC) and back_page.startswith(SYNC)
    for page in (front_page, back_page):
        header = _header(page)
        assert _field(header, 272) == 1 and _field(header, 368) == 0
        assert _field(header, 452) == 2
        assert _field(header, 400) == 19
        assert _floats(header, 424) == (1.0, 595.0, 841.0, 0.0, 0.0, 595.0, 841.0)
        assert (_field(header, 372), _field(header, 376)) == raster_extent(ticket.media.hundredths, ticket.dpi)
        assert (_field(header, 352), _field(header, 356)) == raster_extent(ticket.media.hundredths, 72)
        assert unpack_rows(page[len(SYNC) + HEADER_BYTES:], _field(header, 372), _field(header, 376))
    assert _signed(_header(front_page), 456) == 1 and _signed(_header(front_page), 460) == 1
    assert _signed(_header(back_page), 456) == -1 and _signed(_header(back_page), 460) == -1
    width, height = raster_extent(ticket.media.hundredths, ticket.dpi)
    assert _pixels(back_page) == orient_raster(_source(back, ticket), width, height, -1, -1)


def test_a4_360_dpi_raster_matches_pwg_media_size() -> None:
    assert raster_extent((21000, 29700), 360) == (2976, 4209)
    assert raster_extent((21000, 29700), 72) == (595, 841)


def test_rotated_back_side_is_turned_180() -> None:
    raw = bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    assert orient_raster(raw, 2, 2, -1, -1) == bytes([10, 11, 12, 7, 8, 9, 4, 5, 6, 1, 2, 3])
    assert raster_transform("two-sided-long-edge", "rotated", 1) == (-1, -1)
    assert raster_transform("two-sided-long-edge", "rotated", 0) == (1, 1)


def _floats(header: bytes, offset: int) -> tuple[float, ...]:
    import struct
    return tuple(round(value, 3) for value in struct.unpack(">7f", header[offset:offset + 28]))


def _field(header: bytes, offset: int) -> int:
    return int.from_bytes(header[offset:offset + 4], "big")


def _signed(header: bytes, offset: int) -> int:
    return int.from_bytes(header[offset:offset + 4], "big", signed=True)


def _header(page: bytes) -> bytes:
    return page[len(SYNC):len(SYNC) + HEADER_BYTES]


def _pixels(page: bytes) -> bytes:
    header = _header(page)
    width, height = _field(header, 372), _field(header, 376)
    return unpack_rows(page[len(SYNC) + HEADER_BYTES:], width, height)


def _source(page: Path, ticket: PrintTicket) -> bytes:
    image = Image.open(page).convert("RGB")
    width, height = raster_extent(ticket.media.hundredths, ticket.dpi)
    return image.resize((width, height), Image.Resampling.LANCZOS).tobytes()


def _png(path: Path, raw: bytes) -> Path:
    Image.frombytes("RGB", (2, 2), raw).save(path)
    return path


def _ticket(sheet_back: str) -> PrintTicket:
    return PrintTicket(
        media=MediaSize("iso_a4_210x297mm", (4, 2), (21000, 29700)),
        source="main",
        margin=300,
        color="color",
        quality=5,
        scaling="none",
        sides="two-sided-long-edge",
        dpi=72,
        document_format="image/pwg-raster",
        sheet_back=sheet_back,
    )
