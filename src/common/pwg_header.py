import struct

HEADER_BYTES = 1796
SYNC = b"RaS2"
SRGB = 19


def pwg_page(
    raw: bytes,
    width: int,
    height: int,
    dpi: int,
    points: tuple[int, int],
    page_name: str,
    sides: str = "one-sided",
    page_count: int = 1,
    cross: int = 1,
    feed: int = 1,
) -> bytes:
    from common.pwg_rows import pack_rows

    header = page_header(width, height, dpi, points, page_name, sides, page_count, cross, feed)
    return SYNC + header + pack_rows(raw, width, height)


def page_header(
    width: int,
    height: int,
    dpi: int,
    points: tuple[int, int],
    page_name: str,
    sides: str = "one-sided",
    page_count: int = 1,
    cross: int = 1,
    feed: int = 1,
) -> bytes:
    header = bytearray(HEADER_BYTES)
    _text(header, 0, "PwgRaster")
    _text(header, 128, "stationery")
    _u32(header, 276, dpi)
    _u32(header, 280, dpi)
    _u32(header, 292, points[0])
    _u32(header, 296, points[1])
    _u32(header, 340, 1)
    _u32(header, 352, points[0])
    _u32(header, 356, points[1])
    _u32(header, 372, width)
    _u32(header, 376, height)
    _u32(header, 384, 8)
    _u32(header, 388, 24)
    _u32(header, 392, width * 3)
    _u32(header, 400, SRGB)
    _u32(header, 420, 3)
    _f32(header, 424, 1.0)
    _f32(header, 428, points[0])
    _f32(header, 432, points[1])
    _f32(header, 436, 0.0)
    _f32(header, 440, 0.0)
    _f32(header, 444, points[0])
    _f32(header, 448, points[1])
    _u32(header, 452, page_count)
    _s32(header, 456, cross)
    _s32(header, 460, feed)
    _u32(header, 472, width)
    _u32(header, 476, height)
    _u32(header, 480, 0xFFFFFF)
    _text(header, 1732, page_name)
    _mark_sides(header, sides)
    return bytes(header)


def _mark_sides(header: bytearray, sides: str) -> None:
    if sides not in ("two-sided-long-edge", "two-sided-short-edge"):
        return
    _u32(header, 272, 1)
    if sides == "two-sided-short-edge":
        _u32(header, 368, 1)


def _text(header: bytearray, offset: int, value: str) -> None:
    raw = value.encode()[:63]
    header[offset:offset + len(raw)] = raw


def _f32(header: bytearray, offset: int, value: float) -> None:
    header[offset:offset + 4] = struct.pack(">f", float(value))


def _u32(header: bytearray, offset: int, value: int) -> None:
    header[offset:offset + 4] = struct.pack(">I", value)


def _s32(header: bytearray, offset: int, value: int) -> None:
    header[offset:offset + 4] = struct.pack(">i", value)

