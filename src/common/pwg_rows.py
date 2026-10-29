def pack_rows(raw: bytes, width: int, height: int) -> bytes:
    stride = width * 3
    if len(raw) != stride * height:
        raise ValueError("RGB buffer does not match the raster size")
    packed = bytearray()
    row = 0
    while row < height:
        start = row * stride
        line = raw[start:start + stride]
        repeat = 1
        while repeat < 256 and row + repeat < height:
            nxt = (row + repeat) * stride
            if raw[nxt:nxt + stride] != line:
                break
            repeat += 1
        packed.append(repeat - 1)
        packed.extend(pack_line(line, 3))
        row += repeat
    return bytes(packed)


def pack_line(pixels: bytes, bpp: int) -> bytes:
    out = bytearray()
    pend = len(pixels)
    last = pend - bpp
    ptr = 0
    while ptr < pend:
        start = ptr
        ptr += bpp
        if ptr >= pend:
            out.append(0)
            out.extend(pixels[start:start + bpp])
            break
        if pixels[start:start + bpp] == pixels[ptr:ptr + bpp]:
            ptr, count = _repeat(pixels, ptr, bpp, last)
            out.append(count - 1)
            out.extend(pixels[ptr:ptr + bpp])
            ptr += bpp
        else:
            ptr, count = _literal(pixels, ptr, bpp, last)
            out.append((257 - count) & 0xFF)
            out.extend(pixels[start:start + count * bpp])
    return bytes(out)


def unpack_rows(payload: bytes, width: int, height: int) -> bytes:
    stride = width * 3
    raw = bytearray()
    offset = 0
    while len(raw) < stride * height:
        repeat = payload[offset] + 1
        line, offset = unpack_line(payload, offset + 1, 3, stride)
        raw.extend(line * repeat)
    return bytes(raw)


def unpack_line(payload: bytes, offset: int, bpp: int, expected: int) -> tuple[bytes, int]:
    pixels = bytearray()
    while len(pixels) < expected:
        flag = payload[offset]
        offset += 1
        if flag < 128:
            count = flag + 1
            pixel = payload[offset:offset + bpp]
            offset += bpp
            pixels.extend(pixel * count)
        else:
            count = 257 - flag
            take = count * bpp
            pixels.extend(payload[offset:offset + take])
            offset += take
    return bytes(pixels), offset


def _repeat(pixels: bytes, ptr: int, bpp: int, last: int) -> tuple[int, int]:
    count = 2
    while count < 128 and ptr < last and pixels[ptr:ptr + bpp] == pixels[ptr + bpp:ptr + 2 * bpp]:
        count += 1
        ptr += bpp
    return ptr, count


def _literal(pixels: bytes, ptr: int, bpp: int, last: int) -> tuple[int, int]:
    count = 1
    while count < 128 and ptr < last and pixels[ptr:ptr + bpp] != pixels[ptr + bpp:ptr + 2 * bpp]:
        count += 1
        ptr += bpp
    if ptr >= last and count < 128:
        return ptr + bpp, count + 1
    return ptr, count
