import logging
import socket
import sys
from typing import NamedTuple, Protocol

from common.net_interfaces import ipv4_interfaces

logger = logging.getLogger(__name__)

MDNS_ADDRESS = ("224.0.0.251", 5353)
_GROUP = "224.0.0.251"
_PORT = 5353


class MulticastSender(Protocol):
    def sendto(self, payload: bytes, address: tuple[str, int]) -> int: ...


class MdnsPorts(NamedTuple):
    listener: socket.socket | None
    senders: tuple[socket.socket, ...]


def open_mdns_ports() -> MdnsPorts:
    return MdnsPorts(_listener(), _senders())


def close_mdns_ports(ports: MdnsPorts) -> None:
    for sock in mdns_sockets(ports):
        sock.close()


def mdns_sockets(ports: MdnsPorts) -> tuple[socket.socket, ...]:
    if ports.listener is None:
        return ports.senders
    return (ports.listener, *ports.senders)


def enable_reuse(sock: socket.socket, platform_name: str) -> None:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if platform_name != "darwin" or not hasattr(socket, "SO_REUSEPORT"):
        return
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except OSError as exc:
        logger.warning("Could not set SO_REUSEPORT: %s", exc)


def bind_mdns(sock: socket.socket, port: int) -> int:
    try:
        sock.bind(("", port))
    except OSError:
        sock.bind(("", 0))
    return int(sock.getsockname()[1])


def send_queries(senders: list[MulticastSender], queries: list[bytes]) -> None:
    for sender in senders:
        _send(sender, queries)


def _listener() -> socket.socket | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        enable_reuse(sock, sys.platform)
        if bind_mdns(sock, _PORT) != _PORT:
            sock.close()
            return None
        for addr in ipv4_interfaces() or ("0.0.0.0",):
            _join(sock, addr)
        sock.setblocking(False)
        return sock
    except OSError as exc:
        logger.info("mDNS multicast listener was not opened: %s", exc)
        sock.close()
        return None


def _senders() -> tuple[socket.socket, ...]:
    opened = [_open_sender(addr) for addr in ipv4_interfaces()]
    senders = tuple(sock for sock in opened if sock is not None)
    if senders:
        return senders
    return (_default_sender(),)


def _open_sender(addr: str) -> socket.socket | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        _hop_limit(sock)
        _outgoing_interface(sock, addr)
        sock.bind((addr, 0))
        sock.setblocking(False)
        return sock
    except OSError as exc:
        logger.warning("mDNS sender on %s was not opened: %s", addr, exc)
        sock.close()
        return None


def _default_sender() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    _hop_limit(sock)
    sock.bind(("", 0))
    sock.setblocking(False)
    return sock


def _hop_limit(sock: socket.socket) -> None:
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
    except OSError:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, b"\xff")


def _join(sock: socket.socket, addr: str) -> None:
    membership = socket.inet_aton(_GROUP) + socket.inet_aton(addr)
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
    except OSError as exc:
        logger.warning("Could not join mDNS on %s: %s", addr, exc)


def _outgoing_interface(sock: socket.socket, addr: str) -> None:
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(addr))


def _send(sock: MulticastSender, queries: list[bytes]) -> None:
    for query in queries:
        try:
            sock.sendto(query, MDNS_ADDRESS)
        except OSError as exc:
            logger.debug("mDNS query was not sent: %s", exc)
