import struct

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
    assert struct.unpack(">f", header[424:428]) == (1.0,)
    assert unpack_rows(page[len(SYNC) + HEADER_BYTES:], width, height) == raw
    assert page_header(width, height, 360, (595, 842), "iso_a4_210x297mm") == header
