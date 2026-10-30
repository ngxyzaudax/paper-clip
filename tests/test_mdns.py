import struct

from common.device_uri import printer_uri, scanner_uri
from common.mdns_name import encode_dns_name, read_dns_name
from common.mdns_parse import Service, parse_packet, services_from_records


def test_dns_name_follows_a_pointer() -> None:
    packet = encode_dns_name("_ipp._tcp.local") + b"\xc0\x00"
    name, offset = read_dns_name(packet, len(packet) - 2)
    assert name == "_ipp._tcp.local"
    assert offset == len(packet)


def test_ptr_without_srv_is_ignored() -> None:
    service_type = "_ipp._tcp.local"
    instance = "EPSON ET-8500 Series._ipp._tcp.local"
    packet = _response((_record(service_type, 12, encode_dns_name(instance)),))
    assert services_from_records(parse_packet(packet), service_type) == []


def test_ipp_service_uses_address_port_and_resource() -> None:
    service_type = "_ipp._tcp.local"
    instance = "EPSON ET-8500 Series._ipp._tcp.local"
    host = "printer.local"
    packet = _response((
        _record(service_type, 12, encode_dns_name(instance)),
        _record(instance, 33, struct.pack(">HHH", 0, 0, 631) + encode_dns_name(host)),
        _record(instance, 16, _txt(("rp", "ipp/print"), ("ty", "ET-8500"), ("UUID", "abc"))),
        _record(host, 1, bytes((192, 168, 1, 2))),
    ))
    found = services_from_records(parse_packet(packet), service_type)
    assert len(found) == 1
    assert found[0].instance == "EPSON ET-8500 Series"
    assert found[0].port == 631
    assert found[0].addresses == ("192.168.1.2",)
    assert found[0].txt["rp"] == "ipp/print"
    assert printer_uri(found[0]) == "ipp://192.168.1.2:631/ipp/print"


def test_uscan_service_uses_https_on_port_443() -> None:
    service = Service("_uscan._tcp.local", "EPSON ET-8500 Series", "printer.local", 443, ("192.168.1.2",), {"rs": "eSCL"})
    assert scanner_uri(service) == "https://192.168.1.2:443"


def _response(records: tuple[bytes, ...]) -> bytes:
    return struct.pack(">HHHHHH", 0, 0x8400, 0, len(records), 0, 0) + b"".join(records)


def _record(name: str, kind: int, data: bytes) -> bytes:
    return encode_dns_name(name) + struct.pack(">HHIH", kind, 1, 120, len(data)) + data


def _txt(first: tuple[str, str], *rest: tuple[str, str]) -> bytes:
    encoded = bytearray()
    for key, value in (first, *rest):
        piece = f"{key}={value}".encode()
        encoded.append(len(piece))
        encoded.extend(piece)
    return bytes(encoded)
