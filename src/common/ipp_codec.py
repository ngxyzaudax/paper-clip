import struct
from typing import NamedTuple

END = b"\x03"
BEGIN_COLLECTION = 0x34
END_COLLECTION = 0x37
MEMBER_NAME = 0x4A
DELIMITER_MAX = 0x0F

type IppValue = object
type IppMap = dict[str, list[IppValue]]


class IppMessage(NamedTuple):
    status: int
    request_id: int
    attributes: IppMap
    unsupported: tuple[str, ...]


def pack_message(operation: int, request_id: int, body: bytes) -> bytes:
    return struct.pack(">BBHI", 2, 0, operation, request_id) + body + END


def attr_bytes(tag: int, name: str, value: bytes) -> bytes:
    raw_name = name.encode()
    return bytes([tag]) + struct.pack(">H", len(raw_name)) + raw_name + struct.pack(">H", len(value)) + value


def attr_text(tag: int, name: str, value: str) -> bytes:
    return attr_bytes(tag, name, value.encode())


def attr_integer(tag: int, name: str, value: int) -> bytes:
    return attr_bytes(tag, name, struct.pack(">i", value))


def attr_bool(name: str, value: bool) -> bytes:
    return attr_bytes(0x22, name, b"\x01" if value else b"\x00")


def attr_resolution(name: str, x_dpi: int, y_dpi: int) -> bytes:
    return attr_bytes(0x32, name, struct.pack(">iiB", x_dpi, y_dpi, 3))


def begin_collection(name: str) -> bytes:
    return attr_bytes(BEGIN_COLLECTION, name, b"")


def member(name: str) -> bytes:
    return attr_bytes(MEMBER_NAME, "", name.encode())


def end_collection() -> bytes:
    return attr_bytes(END_COLLECTION, "", b"")


def group(tag: int) -> bytes:
    return bytes([tag])


def unpack_message(payload: bytes) -> IppMessage:
    if len(payload) < 8:
        raise ValueError("IPP response is too short")
    status, request_id = struct.unpack(">HI", payload[2:8])
    attributes, unsupported = _read_groups(payload, 8)
    return IppMessage(status, request_id, attributes, unsupported)


def _read_groups(payload: bytes, offset: int) -> tuple[IppMap, tuple[str, ...]]:
    merged: IppMap = {}
    unsupported: list[str] = []
    while offset < len(payload):
        tag = payload[offset]
        if tag == 0x03:
            break
        if tag > DELIMITER_MAX:
            raise ValueError(f"expected an IPP group tag, got {tag:#x}")
        offset += 1
        values, offset = _read_group(payload, offset)
        if tag == 0x05:
            unsupported.extend(values.keys())
            continue
        for name, items in values.items():
            merged.setdefault(name, []).extend(items)
    return merged, tuple(unsupported)


def _read_group(payload: bytes, offset: int) -> tuple[IppMap, int]:
    values: IppMap = {}
    last_name = ""
    pending = ""
    while offset < len(payload):
        tag = payload[offset]
        if tag <= DELIMITER_MAX:
            return values, offset
        offset += 1
        name, offset = _counted_text(payload, offset)
        raw, offset = _counted_bytes(payload, offset)
        if tag == END_COLLECTION:
            return values, offset
        if tag == MEMBER_NAME:
            pending = raw.decode()
            continue
        key = name or pending or last_name
        pending = ""
        if tag == BEGIN_COLLECTION:
            members, offset = _read_group(payload, offset)
            values.setdefault(key, []).append(members)
        else:
            values.setdefault(key, []).append(_decode_value(tag, raw))
        last_name = key
    return values, offset


def _counted_text(payload: bytes, offset: int) -> tuple[str, int]:
    raw, offset = _counted_bytes(payload, offset)
    return raw.decode(), offset


def _counted_bytes(payload: bytes, offset: int) -> tuple[bytes, int]:
    length = struct.unpack(">H", payload[offset:offset + 2])[0]
    start = offset + 2
    end = start + length
    return payload[start:end], end


def _decode_value(tag: int, raw: bytes) -> IppValue:
    if tag in (0x21, 0x23) and len(raw) == 4:
        return struct.unpack(">i", raw)[0]
    if tag == 0x22 and raw:
        return raw[0] == 1
    if tag == 0x32 and len(raw) == 9:
        x_dpi, y_dpi, units = struct.unpack(">iiB", raw)
        return (x_dpi, y_dpi, units)
    if tag == 0x33 and len(raw) == 8:
        return struct.unpack(">ii", raw)
    if tag in (0x41, 0x42, 0x44, 0x45, 0x47, 0x48, 0x49):
        return raw.decode()
    return raw
