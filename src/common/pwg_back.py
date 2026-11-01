_BACK: dict[tuple[str, str], tuple[int, int]] = {
    ("two-sided-long-edge", "flipped"): (1, -1),
    ("two-sided-long-edge", "manual-tumble"): (1, 1),
    ("two-sided-long-edge", "normal"): (1, 1),
    ("two-sided-long-edge", "rotated"): (-1, -1),
    ("two-sided-short-edge", "flipped"): (-1, 1),
    ("two-sided-short-edge", "manual-tumble"): (-1, -1),
    ("two-sided-short-edge", "normal"): (1, 1),
    ("two-sided-short-edge", "rotated"): (1, 1),
}


def raster_extent(hundredths: tuple[int, int], scale: int) -> tuple[int, int]:
    return (hundredths[0] * scale // 2540, hundredths[1] * scale // 2540)


def raster_transform(sides: str, sheet_back: str, index: int) -> tuple[int, int]:
    if index % 2 == 0 or sides == "one-sided":
        return (1, 1)
    return _BACK.get((sides, sheet_back), (1, 1))


def orient_raster(raw: bytes, width: int, height: int, cross: int, feed: int) -> bytes:
    if cross == 1 and feed == 1:
        return raw
    rows = _rows(raw, width * 3, height)
    ordered = list(reversed(rows)) if feed < 0 else rows
    turned = [_reverse_row(row) for row in ordered] if cross < 0 else ordered
    return b"".join(turned)


def _rows(raw: bytes, stride: int, height: int) -> list[bytes]:
    return [raw[index * stride:(index + 1) * stride] for index in range(height)]


def _reverse_row(row: bytes) -> bytes:
    flipped = bytearray(len(row))
    offset = 0
    while offset < len(row):
        start = len(row) - offset - 3
        flipped[start:start + 3] = row[offset:offset + 3]
        offset += 3
    return bytes(flipped)
