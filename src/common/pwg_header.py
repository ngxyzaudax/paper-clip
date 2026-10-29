import struct

HEADER_BYTES = 1796
SYNC = b"RaS2"
SRGB = 19


def pwg_page(raw: bytes, width: int, height: int, dpi: int, points: tuple[int, int], page_name: str) -> bytes:
    from common.pwg_rows import pack_rows

    header = page_header(width, height, dpi, points, page_name)
    return SYNC + header + pack_rows(raw, width, height)


def page_header(width: int, height: int, dpi: int, points: tuple[int, int], page_name: str) -> bytes:
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
    _f32(header, 428, float(points[0]))
    _f32(header, 432, float(points[1]))
    _f32(header, 444, float(points[0]))
    _f32(header, 448, float(points[1]))
    _u32(header, 452, 1)
    _u32(header, 456, 1)
    _u32(header, 460, 1)
    _u32(header, 472, width)
    _u32(header, 476, height)
    _u32(header, 480, 0xFFFFFF)
    _text(header, 1732, page_name)
    return bytes(header)


def _text(header: bytearray, offset: int, value: str) -> None:
    raw = value.encode()[:63]
    header[offset:offset + len(raw)] = raw


def _u32(header: bytearray, offset: int, value: int) -> None:
    header[offset:offset + 4] = struct.pack(">I", value)


def _f32(header: bytearray, offset: int, value: float) -> None:
    header[offset:offset + 4] = struct.pack(">f", value)
