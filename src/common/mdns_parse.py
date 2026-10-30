import struct
from typing import NamedTuple

from common.mdns_name import read_dns_name

_PTR = 12
_TXT = 16
_AAAA = 28
_SRV = 33
_A = 1


class Record(NamedTuple):
    name: str
    kind: int
    data: bytes
    target: str


class Service(NamedTuple):
    service_type: str
    instance: str
    host: str
    port: int
    addresses: tuple[str, ...]
    txt: dict[str, str]


def parse_packet(packet: bytes) -> list[Record]:
    if len(packet) < 12:
        return []
    questions, answers, authorities, additional = struct.unpack(">HHHH", packet[4:12])
    offset = _skip_questions(packet, 12, questions)
    records: list[Record] = []
    for _ in range(answers + authorities + additional):
        if offset >= len(packet):
            break
        record, offset = _read_record(packet, offset)
        records.append(record)
    return records


def services_from_records(records: list[Record], service_type: str) -> list[Service]:
    wanted = service_type.lower()
    instances = [
        record.target
        for record in records
        if record.kind == _PTR and record.name.lower() == wanted and record.target
    ]
    services = [_service(records, service_type, instance) for instance in dict.fromkeys(instances)]
    return [service for service in services if service.port]


def _service(records: list[Record], service_type: str, instance: str) -> Service:
    host, port = _srv(records, instance)
    return Service(
        service_type=service_type,
        instance=_label(instance, service_type),
        host=host,
        port=port,
        addresses=_addresses(records, host),
        txt=_txt(records, instance),
    )


def _srv(records: list[Record], instance: str) -> tuple[str, int]:
    for record in records:
        if record.kind == _SRV and _same(record.name, instance) and len(record.data) >= 6:
            return record.target, struct.unpack(">H", record.data[4:6])[0]
    return "", 0


def _addresses(records: list[Record], host: str) -> tuple[str, ...]:
    found = [
        ".".join(str(byte) for byte in record.data)
        for record in records
        if record.kind == _A and _same(record.name, host) and len(record.data) == 4
    ]
    found.extend(
        _ipv6(record.data)
        for record in records
        if record.kind == _AAAA and _same(record.name, host) and len(record.data) == 16
    )
    return tuple(dict.fromkeys(found))


def _txt(records: list[Record], instance: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for record in records:
        if record.kind == _TXT and _same(record.name, instance):
            values.update(_txt_pairs(record.data))
    return values


def _txt_pairs(data: bytes) -> dict[str, str]:
    pairs: dict[str, str] = {}
    offset = 0
    while offset < len(data):
        length = data[offset]
        offset += 1
        piece = data[offset:offset + length].decode("utf-8", "replace")
        offset += length
        key, _, value = piece.partition("=")
        if key:
            pairs[key] = value
    return pairs


def _label(instance: str, service_type: str) -> str:
    suffix = "." + service_type
    if instance.lower().endswith(suffix.lower()):
        return instance[: -len(suffix)]
    return instance


def _ipv6(data: bytes) -> str:
    parts = [f"{int.from_bytes(data[index:index + 2], 'big'):x}" for index in range(0, 16, 2)]
    return ":".join(parts)


def _skip_questions(packet: bytes, offset: int, count: int) -> int:
    for _ in range(count):
        _, offset = read_dns_name(packet, offset)
        offset += 4
    return offset


def _read_record(packet: bytes, offset: int) -> tuple[Record, int]:
    name, offset = read_dns_name(packet, offset)
    kind, _klass, _ttl, length = struct.unpack(">HHIH", packet[offset:offset + 10])
    start = offset + 10
    target = ""
    if kind == _PTR:
        target, _ = read_dns_name(packet, start)
    elif kind == _SRV and length >= 6:
        target, _ = read_dns_name(packet, start + 6)
    return Record(name, kind, packet[start:start + length], target), start + length


def _same(left: str, right: str) -> bool:
    return left.lower() == right.lower()
