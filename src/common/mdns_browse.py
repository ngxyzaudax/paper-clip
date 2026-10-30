import logging
import select
import socket
import struct
import time

from common.mdns_name import encode_dns_name
from common.mdns_parse import Service, parse_packet, services_from_records
from common.mdns_socket import MdnsPorts, close_mdns_ports, mdns_sockets, open_mdns_ports, send_queries

logger = logging.getLogger(__name__)

DRIVERLESS_TYPES = ("_ipp._tcp.local", "_ipps._tcp.local", "_uscan._tcp.local")


def browse_types(service_types: tuple[str, ...] = DRIVERLESS_TYPES, timeout: float = 1.6) -> dict[str, list[Service]]:
    packets = _collect(service_types, timeout)
    records = [record for packet in packets for record in parse_packet(packet)]
    return {service_type: services_from_records(records, service_type) for service_type in service_types}


def _collect(service_types: tuple[str, ...], timeout: float) -> list[bytes]:
    queries = [_question(service_type) for service_type in service_types]
    try:
        ports = open_mdns_ports()
    except OSError as exc:
        logger.warning("mDNS browse failed: %s", exc)
        return []
    try:
        send_queries(list(ports.senders), queries)
        return _receive(ports, queries, timeout)
    except OSError as exc:
        logger.warning("mDNS browse failed: %s", exc)
        return []
    finally:
        close_mdns_ports(ports)


def _receive(ports: MdnsPorts, queries: list[bytes], timeout: float) -> list[bytes]:
    found: list[bytes] = []
    watch = list(mdns_sockets(ports))
    deadline = time.monotonic() + timeout
    while True:
        wait = deadline - time.monotonic()
        if wait <= 0:
            return found
        readable, _, _ = select.select(watch, [], [], min(0.25, wait))
        if not readable:
            send_queries(list(ports.senders), queries)
            continue
        for sock in readable:
            found.extend(_read(sock))
    return found


def _read(sock: socket.socket) -> list[bytes]:
    found: list[bytes] = []
    while True:
        try:
            data, _addr = sock.recvfrom(9000)
        except BlockingIOError:
            return found
        except OSError as exc:
            logger.debug("mDNS receive failed: %s", exc)
            return found
        found.append(data)


def _question(name: str) -> bytes:
    header = struct.pack(">HHHHHH", 0, 0, 1, 0, 0, 0)
    return header + encode_dns_name(name) + struct.pack(">HH", 12, 0x8001)
