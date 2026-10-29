import logging
import socket
import struct
import time

from common.mdns_name import encode_dns_name
from common.mdns_parse import Service, parse_packet, services_from_records

logger = logging.getLogger(__name__)

DRIVERLESS_TYPES = ("_ipp._tcp.local", "_ipps._tcp.local", "_uscan._tcp.local")
_MDNS = ("224.0.0.251", 5353)


def browse_types(service_types: tuple[str, ...] = DRIVERLESS_TYPES, timeout: float = 1.6) -> dict[str, list[Service]]:
    packets = _collect(service_types, timeout)
    records = [record for packet in packets for record in parse_packet(packet)]
    return {service_type: services_from_records(records, service_type) for service_type in service_types}


def _collect(service_types: tuple[str, ...], timeout: float) -> list[bytes]:
    queries = [_question(service_type) for service_type in service_types]
    try:
        with _socket() as sock:
            for query in queries:
                sock.sendto(query, _MDNS)
            return _receive(sock, queries, timeout)
    except OSError as exc:
        logger.warning("mDNS browse failed: %s", exc)
        return []


def _socket() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
    sock.settimeout(0.25)
    return sock


def _receive(sock: socket.socket, queries: list[bytes], timeout: float) -> list[bytes]:
    found: list[bytes] = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            data, _addr = sock.recvfrom(9000)
        except TimeoutError:
            for query in queries:
                sock.sendto(query, _MDNS)
            continue
        found.append(data)
    return found


def _question(name: str) -> bytes:
    header = struct.pack(">HHHHHH", 0, 0, 1, 0, 0, 0)
    return header + encode_dns_name(name) + struct.pack(">HH", 12, 0x8001)
